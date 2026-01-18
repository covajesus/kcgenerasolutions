from datetime import datetime, time
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session
import re
from pathlib import Path
import zlib

from app.backend.auth.auth_user import get_current_active_user
from app.backend.db.database import get_db
from app.backend.db.models import ExpenseReportModel, UserModel
from app.backend.schemas import ReportGenerate


reports = APIRouter(
    prefix="/reports",
    tags=["Reports"],
)


def _parse_date(value: str) -> datetime:
    """
    Acepta:
    - YYYY-MM-DD
    - YYYY-MM-DD HH:MM:SS
    - ISO (YYYY-MM-DDTHH:MM:SS)
    """
    v = (value or "").strip()
    if not v:
        raise ValueError("empty date")

    # ISO-like
    try:
        return datetime.fromisoformat(v.replace("Z", ""))
    except Exception:
        pass

    for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S"):
        try:
            dt = datetime.strptime(v, fmt)
            if fmt == "%Y-%m-%d":
                # por defecto al inicio del día
                return datetime.combine(dt.date(), time.min)
            return dt
        except Exception:
            continue

    raise ValueError("invalid date format")


def _pdf_escape(text: str) -> str:
    return (text or "").replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _approx_text_width(text: str, font_size: int) -> float:
    # Aproximación para Helvetica: ~0.5 * font_size por caracter
    return max(0.0, len(text or "") * font_size * 0.5)


def _parse_amount(value) -> float | None:
    """
    Convierte montos guardados como string a número.

    Soporta:
    - "1234"
    - "1,234.56"  (en-US)
    - "1.234,56"  (es-CL)
    - "$ 1.234" / "USD 1,234"
    """
    if value is None:
        return None
    s = str(value).strip()
    if not s:
        return None

    # Dejar solo dígitos y separadores comunes
    cleaned = re.sub(r"[^0-9\.,\-]", "", s)
    if not cleaned or cleaned == "-" or cleaned == "," or cleaned == ".":
        return None

    # Si tiene ambos separadores, asumir miles/decimales según orden
    if "," in cleaned and "." in cleaned:
        if cleaned.rfind(",") > cleaned.rfind("."):
            # "1.234,56" -> miles '.' y decimal ','
            cleaned = cleaned.replace(".", "").replace(",", ".")
        else:
            # "1,234.56" -> miles ',' y decimal '.'
            cleaned = cleaned.replace(",", "")
    elif "," in cleaned:
        # "1234,56" -> decimal ','
        cleaned = cleaned.replace(",", ".")

    try:
        return float(cleaned)
    except Exception:
        return None


def _format_currency(amount: float) -> str:
    # Inglés: miles con coma, decimales con punto
    if amount == int(amount):
        return f"${int(amount):,}"
    return f"${amount:,.2f}"


def _build_expense_report_pdf(
    since_dt: datetime,
    end_dt: datetime,
    rows: List[ExpenseReportModel],
) -> bytes:
    """
    PDF (sin libs externas) con título centrado + tabla.
    """
    objects: List[bytes] = []

    def add_obj(data: bytes) -> int:
        objects.append(data)
        return len(objects)  # 1-based obj number

    # Fonts
    font_regular = add_obj(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    font_bold = add_obj(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>")

    # Logo (opcional). Preferir PNG y dejar WEBP como fallback.
    logo_obj = None
    logo_px_w = None
    logo_px_h = None
    try:
        from PIL import Image  # type: ignore

        project_root = Path(__file__).resolve().parents[3]
        # Preferido: logo.png. Fallback: logo.webp
        logo_path = project_root / "public" / "assets" / "logo.png"
        if not (logo_path.exists() and logo_path.is_file()):
            logo_path = project_root / "public" / "assets" / "logo.webp"
        if logo_path.exists() and logo_path.is_file():
            with Image.open(str(logo_path)) as img:
                # Si el PNG trae transparencia (alpha), al convertir directo a RGB queda fondo negro.
                # Lo aplanamos sobre fondo blanco para que se vea bien.
                img = img.convert("RGBA")
                bg = Image.new("RGBA", img.size, (255, 255, 255, 255))
                img = Image.alpha_composite(bg, img).convert("RGB")
                # Limitar tamaño en píxeles para que el PDF no quede pesado
                max_px_w = 600
                if img.width > max_px_w:
                    ratio = max_px_w / float(img.width)
                    new_size = (max_px_w, max(1, int(img.height * ratio)))
                    img = img.resize(new_size)

                logo_px_w, logo_px_h = img.width, img.height
                raw = img.tobytes()  # RGB, 8 bits por canal
                compressed = zlib.compress(raw, level=9)

                logo_obj = add_obj(
                    b"<< /Type /XObject /Subtype /Image "
                    + b"/Width " + str(logo_px_w).encode("ascii")
                    + b" /Height " + str(logo_px_h).encode("ascii")
                    + b" /ColorSpace /DeviceRGB /BitsPerComponent 8 "
                    + b"/Filter /FlateDecode "
                    + b"/Length " + str(len(compressed)).encode("ascii")
                    + b" >>\nstream\n"
                    + compressed
                    + b"\nendstream"
                )
    except Exception:
        # No romper el reporte si falta el archivo o Pillow
        logo_obj = None
        logo_px_w = None
        logo_px_h = None

    # Layout constants
    page_width = 612
    page_height = 792
    margin_x = 40

    # Bajar título/fecha para separarlos del logo
    title_y = 650
    range_y = 625
    table_top = 595
    header_h = 22
    row_h = 18
    table_width = page_width - (margin_x * 2)  # 532

    # Columns
    # Agregar columna Description en el PDF
    col_date = 90
    col_doc = 110
    col_company = 150
    col_amount = 92
    col_desc = table_width - (col_date + col_doc + col_company + col_amount)

    x0 = margin_x
    x1 = x0 + col_date
    x2 = x1 + col_doc
    x3 = x2 + col_company
    x4 = x3 + col_desc
    x5 = x0 + table_width

    title = "Expense Report"
    title_size = 18
    title_x = (page_width / 2.0) - (_approx_text_width(title, title_size) / 2.0)
    title_x = max(margin_x, min(title_x, page_width - margin_x))

    range_text = f"From: {since_dt.strftime('%Y-%m-%d %H:%M:%S')}    To: {end_dt.strftime('%Y-%m-%d %H:%M:%S')}"

    # Prepare line strings
    table_rows: List[List[str]] = []
    total_amount = 0.0
    total_amount_has_value = False
    for r in rows:
        date_str = r.document_date.strftime("%Y-%m-%d") if r.document_date else ""
        # En DB puede venir int (datos antiguos). Forzar a string siempre.
        doc_str = str(r.document_number) if r.document_number is not None else ""
        company = str(r.company) if r.company is not None else ""
        desc = str(getattr(r, "description", "") or "")

        amount_value = _parse_amount(r.amount)
        if amount_value is not None:
            total_amount += amount_value
            total_amount_has_value = True
            amount = _format_currency(amount_value)
        else:
            # fallback: mostrar con símbolo si viene texto
            raw_amount = str(r.amount) if r.amount is not None else ""
            raw_amount = raw_amount.strip()
            amount = raw_amount
            if amount and not amount.startswith("$"):
                amount = f"$ {amount}"

        # Truncar para la tabla
        if len(doc_str) > 18:
            doc_str = doc_str[:18] + "..."
        if len(company) > 24:
            company = company[:24] + "..."
        if len(desc) > 28:
            desc = desc[:28] + "..."
        if len(amount) > 18:
            amount = amount[:18] + "..."

        table_rows.append([date_str, doc_str, company, desc, amount])

    if not table_rows:
        table_rows = [["", "", "(Sin resultados en el rango)", "", ""]]

    # Pagination by rows available
    # Compute rows per page (leave footer area)
    # dejar espacio para TOTAL + footer
    table_bottom_min = 110
    usable_h = (table_top - table_bottom_min) - header_h
    rows_per_page = max(1, int(usable_h // row_h))

    page_objs: List[int] = []

    for page_index in range(0, len(table_rows), rows_per_page):
        chunk = table_rows[page_index : page_index + rows_per_page]
        table_bottom = table_top - header_h - (len(chunk) * row_h)
        is_last_page = (page_index + rows_per_page) >= len(table_rows)

        cmds: List[str] = []

        # Logo (arriba-izquierda)
        if logo_obj is not None and logo_px_w and logo_px_h:
            # 3x más grande
            logo_draw_h = 84.0
            logo_draw_w = logo_draw_h * (float(logo_px_w) / float(logo_px_h))
            logo_x = margin_x
            # Pegado arriba con margen, separado del título
            logo_y = page_height - 40 - logo_draw_h
            cmds.append("q")
            cmds.append(f"{logo_draw_w:.2f} 0 0 {logo_draw_h:.2f} {logo_x:.2f} {logo_y:.2f} cm")
            cmds.append("/Im1 Do")
            cmds.append("Q")

        # Title (bold)
        cmds.append("BT")
        cmds.append(f"/F2 {title_size} Tf")
        cmds.append(f"1 0 0 1 {title_x:.2f} {title_y} Tm")
        t = _pdf_escape(title).encode("latin-1", errors="replace").decode("latin-1")
        cmds.append(f"({t}) Tj")
        cmds.append("ET")

        # Date range (bold)
        cmds.append("BT")
        cmds.append("/F2 11 Tf")
        cmds.append(f"1 0 0 1 {margin_x} {range_y} Tm")
        rt = _pdf_escape(range_text).encode("latin-1", errors="replace").decode("latin-1")
        cmds.append(f"({rt}) Tj")
        cmds.append("ET")

        # Header background
        header_bottom = table_top - header_h
        cmds.append("0.95 g")
        cmds.append(f"{x0} {header_bottom} {table_width} {header_h} re f")
        cmds.append("0 g")

        # Grid lines
        cmds.append("0 0 0 RG")
        cmds.append("0.7 w")

        # Outer border
        cmds.append(f"{x0} {table_top} m {x5} {table_top} l S")
        cmds.append(f"{x0} {table_bottom} m {x5} {table_bottom} l S")
        cmds.append(f"{x0} {table_bottom} m {x0} {table_top} l S")
        cmds.append(f"{x5} {table_bottom} m {x5} {table_top} l S")

        # Vertical lines
        cmds.append(f"{x1} {table_bottom} m {x1} {table_top} l S")
        cmds.append(f"{x2} {table_bottom} m {x2} {table_top} l S")
        cmds.append(f"{x3} {table_bottom} m {x3} {table_top} l S")
        cmds.append(f"{x4} {table_bottom} m {x4} {table_top} l S")

        # Header bottom line
        cmds.append(f"{x0} {header_bottom} m {x5} {header_bottom} l S")

        # Row lines
        for i in range(1, len(chunk) + 1):
            y = header_bottom - (i * row_h)
            cmds.append(f"{x0} {y} m {x5} {y} l S")

        # Header labels (bold)
        cmds.append("BT")
        cmds.append("/F2 10 Tf")
        cmds.append(f"1 0 0 1 {x0 + 6} {table_top - 15} Tm (Date) Tj")
        cmds.append(f"1 0 0 1 {x1 + 6} {table_top - 15} Tm (Document #) Tj")
        cmds.append(f"1 0 0 1 {x2 + 6} {table_top - 15} Tm (Company) Tj")
        cmds.append(f"1 0 0 1 {x3 + 6} {table_top - 15} Tm (Description) Tj")
        cmds.append(f"1 0 0 1 {x4 + 6} {table_top - 15} Tm (Amount) Tj")
        cmds.append("ET")

        # Rows (regular)
        cmds.append("BT")
        cmds.append("/F1 10 Tf")
        for i, (c_date, c_doc, c_company, c_desc, c_amount) in enumerate(chunk):
            y_text = header_bottom - (i * row_h) - 13
            c_date = _pdf_escape(c_date).encode("latin-1", errors="replace").decode("latin-1")
            c_doc = _pdf_escape(c_doc).encode("latin-1", errors="replace").decode("latin-1")
            c_company = _pdf_escape(c_company).encode("latin-1", errors="replace").decode("latin-1")
            c_desc = _pdf_escape(c_desc).encode("latin-1", errors="replace").decode("latin-1")
            c_amount = _pdf_escape(c_amount).encode("latin-1", errors="replace").decode("latin-1")

            cmds.append(f"1 0 0 1 {x0 + 6} {y_text} Tm ({c_date}) Tj")
            cmds.append(f"1 0 0 1 {x1 + 6} {y_text} Tm ({c_doc}) Tj")
            cmds.append(f"1 0 0 1 {x2 + 6} {y_text} Tm ({c_company}) Tj")
            cmds.append(f"1 0 0 1 {x3 + 6} {y_text} Tm ({c_desc}) Tj")
            cmds.append(f"1 0 0 1 {x4 + 6} {y_text} Tm ({c_amount}) Tj")
        cmds.append("ET")

        # TOTAL (solo en la última página)
        if is_last_page and total_amount_has_value:
            total_text = f"TOTAL: {_format_currency(total_amount)}"
            total_x = x5 - 6 - _approx_text_width(total_text, 12)
            cmds.append("BT")
            cmds.append("/F2 12 Tf")
            cmds.append(f"1 0 0 1 {total_x:.2f} {table_bottom - 26} Tm ({_pdf_escape(total_text)}) Tj")
            cmds.append("ET")

        # Footer page number
        page_num = (page_index // rows_per_page) + 1
        total_pages = ((len(table_rows) - 1) // rows_per_page) + 1
        footer = f"Página {page_num} de {total_pages}"
        footer_x = page_width - margin_x - _approx_text_width(footer, 9)
        cmds.append("BT")
        cmds.append("/F1 9 Tf")
        cmds.append(f"1 0 0 1 {footer_x:.2f} 40 Tm ({_pdf_escape(footer)}) Tj")
        cmds.append("ET")

        stream = ("\n".join(cmds)).encode("latin-1", errors="replace")
        content_obj = add_obj(
            b"<< /Length " + str(len(stream)).encode("ascii") + b" >>\nstream\n" + stream + b"\nendstream"
        )

        resources = (
            b"<< /Font << /F1 "
            + f"{font_regular} 0 R".encode("ascii")
            + b" /F2 "
            + f"{font_bold} 0 R".encode("ascii")
            + b" >>"
        )
        if logo_obj is not None:
            resources += b" /XObject << /Im1 " + f"{logo_obj} 0 R".encode("ascii") + b" >>"
        resources += b" >>"

        page_obj = add_obj(
            b"<< /Type /Page /Parent 0 0 R /MediaBox [0 0 612 792] "
            + b"/Resources "
            + resources
            + b" /Contents "
            + f"{content_obj} 0 R".encode("ascii")
            + b" >>"
        )
        page_objs.append(page_obj)

    # Pages tree
    kids = b" ".join([f"{n} 0 R".encode("ascii") for n in page_objs])
    pages_obj = add_obj(b"<< /Type /Pages /Kids [" + kids + b"] /Count " + str(len(page_objs)).encode("ascii") + b" >>")

    # Patch each page object to point to pages_obj as parent
    for i, objn in enumerate(page_objs):
        raw = objects[objn - 1]
        objects[objn - 1] = raw.replace(b"/Parent 0 0 R", f"/Parent {pages_obj} 0 R".encode("ascii"))

    # Catalog
    catalog_obj = add_obj(b"<< /Type /Catalog /Pages " + f"{pages_obj} 0 R".encode("ascii") + b" >>")

    # Write file
    out = bytearray()
    out.extend(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")

    xref_positions: List[int] = [0]
    for idx, obj in enumerate(objects, start=1):
        xref_positions.append(len(out))
        out.extend(f"{idx} 0 obj\n".encode("ascii"))
        out.extend(obj)
        out.extend(b"\nendobj\n")

    xref_start = len(out)
    out.extend(f"xref\n0 {len(objects)+1}\n".encode("ascii"))
    out.extend(b"0000000000 65535 f \n")
    for pos in xref_positions[1:]:
        out.extend(f"{pos:010d} 00000 n \n".encode("ascii"))

    out.extend(
        b"trailer\n<< /Size "
        + str(len(objects) + 1).encode("ascii")
        + b" /Root "
        + f"{catalog_obj} 0 R".encode("ascii")
        + b" >>\nstartxref\n"
        + str(xref_start).encode("ascii")
        + b"\n%%EOF\n"
    )
    return bytes(out)


@reports.post("/generate")
def generate(
    filters: ReportGenerate,
    session_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    try:
        since_dt = _parse_date(filters.since_date)
        until_raw = filters.until_date or filters.end_date
        end_dt = _parse_date(until_raw)
    except ValueError:
        raise HTTPException(status_code=400, detail="Formato inválido. Use YYYY-MM-DD o YYYY-MM-DD HH:MM:SS")

    # end_date inclusivo (fin del día si viene sin hora)
    if end_dt.time() == time.min and (until_raw or "").strip().count(":") == 0:
        end_dt = datetime.combine(end_dt.date(), time.max)

    if since_dt > end_dt:
        raise HTTPException(status_code=400, detail="since_date no puede ser mayor que until_date")

    rows = (
        db.query(ExpenseReportModel)
        .filter(ExpenseReportModel.document_date >= since_dt)
        .filter(ExpenseReportModel.document_date <= end_dt)
        # Orden ascendente por fecha de documento (NULL al final)
        .order_by(
            ExpenseReportModel.document_date.is_(None),
            ExpenseReportModel.document_date.asc(),
            ExpenseReportModel.id.asc(),
        )
        .all()
    )

    pdf_bytes = _build_expense_report_pdf(since_dt, end_dt, rows)
    filename = f"expense_reports_{since_dt.strftime('%Y%m%d')}_{end_dt.strftime('%Y%m%d')}.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )

