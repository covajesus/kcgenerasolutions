import os
import platform
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import func, cast, String

from app.backend.classes.file_class import FileClass
from app.backend.db.models import InvoiceModel


class InvoiceClass:
    def __init__(self, db):
        self.db = db

    def _file_url(self, remote_path: str | None):
        if not remote_path:
            return None
        rp = str(remote_path).replace("\\", "/").lstrip("/")

        public_base = (os.environ.get("PUBLIC_BASE_URL") or "").strip().rstrip("/")
        if public_base:
            return f"{public_base}/api/files/view/{rp}"

        if platform.system() == "Linux":
            return f"https://api.kcgeneralsolutions.ca/api/files/view/{rp}"

        return f"http://127.0.0.1:8000/api/files/view/{rp}"

    def get_all(self, page=0, items_per_page=10):
        try:
            base_query = self.db.query(InvoiceModel).order_by(InvoiceModel.id.desc())

            if page > 0:
                total_items = self.db.query(func.count(InvoiceModel.id)).scalar()
                total_pages = (total_items + items_per_page - 1) // items_per_page

                if page < 1 or (total_pages > 0 and page > total_pages):
                    return {"status": "error", "message": "Invalid page number"}

                data = base_query.offset((page - 1) * items_per_page).limit(items_per_page).all()

                if not data:
                    return {"status": "error", "message": "No data found"}

                serialized_data = [{
                    "id": inv.id,
                    "invoice_number": inv.invoice_number,
                    "company": inv.company,
                    "file": inv.file,
                    "file_url": self._file_url(inv.file),
                    "invoice_date": inv.invoice_date.strftime("%Y-%m-%d") if getattr(inv, "invoice_date", None) else None,
                    "added_date": inv.added_date.strftime("%Y-%m-%d %H:%M:%S") if inv.added_date else None,
                    "updated_date": inv.updated_date.strftime("%Y-%m-%d %H:%M:%S") if inv.updated_date else None,
                } for inv in data]

                return {
                    "total_items": total_items,
                    "total_pages": total_pages,
                    "current_page": page,
                    "items_per_page": items_per_page,
                    "data": serialized_data
                }

            data = base_query.all()
            return [{
                "id": inv.id,
                "invoice_number": inv.invoice_number,
                "company": inv.company,
                "file": inv.file,
                "file_url": self._file_url(inv.file),
                "invoice_date": inv.invoice_date.strftime("%Y-%m-%d") if getattr(inv, "invoice_date", None) else None,
                "added_date": inv.added_date.strftime("%Y-%m-%d %H:%M:%S") if inv.added_date else None,
                "updated_date": inv.updated_date.strftime("%Y-%m-%d %H:%M:%S") if inv.updated_date else None,
            } for inv in data]

        except Exception as e:
            return {"status": "error", "message": str(e)}

    def get_list(self):
        try:
            data = self.db.query(InvoiceModel).order_by(InvoiceModel.id.desc()).all()
            return {
                "data": [{
                    "id": inv.id,
                    "invoice_number": inv.invoice_number,
                    "company": inv.company,
                    "invoice_date": inv.invoice_date.strftime("%Y-%m-%d") if getattr(inv, "invoice_date", None) else None,
                } for inv in data]
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def search(self, search_inputs, items_per_page=10):
        """
        Busca por invoice_number (parcial).
        """
        try:
            page = (search_inputs or {}).get("page", 0) or 0
            invoice_number = (search_inputs or {}).get("invoice_number")

            if invoice_number is None or str(invoice_number).strip() == "":
                return {"status": "error", "message": "Debe enviar invoice_number"}

            q = self.db.query(InvoiceModel).order_by(InvoiceModel.id.desc())
            # invoice_number es INT en DB; permitir buscar como string
            q = q.filter(cast(InvoiceModel.invoice_number, String).ilike(f"%{str(invoice_number).strip()}%"))

            if page and page > 0:
                total_items = q.count()
                total_pages = (total_items + items_per_page - 1) // items_per_page

                if page < 1 or (total_pages > 0 and page > total_pages):
                    return {"status": "error", "message": "Invalid page number"}

                data = q.offset((page - 1) * items_per_page).limit(items_per_page).all()
                if not data:
                    return {"status": "error", "message": "No data found"}

                serialized_data = [{
                    "id": inv.id,
                    "invoice_number": inv.invoice_number,
                    "company": inv.company,
                    "file": inv.file,
                    "file_url": self._file_url(inv.file),
                    "invoice_date": inv.invoice_date.strftime("%Y-%m-%d") if getattr(inv, "invoice_date", None) else None,
                    "added_date": inv.added_date.strftime("%Y-%m-%d %H:%M:%S") if inv.added_date else None,
                    "updated_date": inv.updated_date.strftime("%Y-%m-%d %H:%M:%S") if inv.updated_date else None,
                } for inv in data]

                return {
                    "total_items": total_items,
                    "total_pages": total_pages,
                    "current_page": page,
                    "items_per_page": items_per_page,
                    "data": serialized_data
                }

            data = q.all()
            return [{
                "id": inv.id,
                "invoice_number": inv.invoice_number,
                "company": inv.company,
                "file": inv.file,
                "file_url": self._file_url(inv.file),
                "invoice_date": inv.invoice_date.strftime("%Y-%m-%d") if getattr(inv, "invoice_date", None) else None,
                "added_date": inv.added_date.strftime("%Y-%m-%d %H:%M:%S") if inv.added_date else None,
                "updated_date": inv.updated_date.strftime("%Y-%m-%d %H:%M:%S") if inv.updated_date else None,
            } for inv in data]

        except Exception as e:
            return {"status": "error", "message": str(e)}

    def store(self, payload: dict):
        try:
            inv_num = payload.get("invoice_number")
            if inv_num is None or str(inv_num).strip() == "":
                return {"status": "error", "message": "invoice_number es requerido"}
            try:
                inv_num = int(inv_num)
            except Exception:
                return {"status": "error", "message": "invoice_number inválido"}

            inv = InvoiceModel(
                invoice_number=inv_num,
                company=str(payload.get("company") or ""),
                file=payload.get("file"),
                invoice_date=payload.get("invoice_date"),
                added_date=datetime.utcnow(),
                updated_date=datetime.utcnow(),
            )
            self.db.add(inv)
            self.db.commit()
            self.db.refresh(inv)
            return {
                "status": "Factura registrada exitosamente.",
                "invoice_id": inv.id,
                "file": inv.file,
                "file_url": self._file_url(inv.file),
                "invoice_date": inv.invoice_date.strftime("%Y-%m-%d") if getattr(inv, "invoice_date", None) else None,
            }
        except Exception as e:
            self.db.rollback()
            return {"status": "error", "message": str(e)}

    def update(self, id: int, payload: dict):
        inv = self.db.query(InvoiceModel).filter(InvoiceModel.id == id).one_or_none()
        if not inv:
            return "No data found"

        try:
            inv_num = payload.get("invoice_number")
            if inv_num is None or str(inv_num).strip() == "":
                return {"status": "error", "message": "invoice_number es requerido"}
            try:
                inv.invoice_number = int(inv_num)
            except Exception:
                return {"status": "error", "message": "invoice_number inválido"}

            inv.company = str(payload.get("company") or "")
            if isinstance(payload, dict) and "file" in payload and payload.get("file") is not None:
                inv.file = payload.get("file")
            if isinstance(payload, dict) and "invoice_date" in payload:
                inv.invoice_date = payload.get("invoice_date")
            inv.updated_date = datetime.utcnow()
            self.db.commit()
            self.db.refresh(inv)
            return {
                "status": "Invoice updated successfully",
                "invoice_id": inv.id,
                "file": inv.file,
                "file_url": self._file_url(inv.file),
                "invoice_date": inv.invoice_date.strftime("%Y-%m-%d") if getattr(inv, "invoice_date", None) else None,
            }
        except Exception as e:
            self.db.rollback()
            return {"status": "error", "message": str(e)}

    def get(self, id: int):
        try:
            inv = self.db.query(InvoiceModel).filter(InvoiceModel.id == id).first()
            if not inv:
                return {"error": "No se encontraron datos para el campo especificado."}
            return {
                "invoice_data": {
                    "id": inv.id,
                    "invoice_number": inv.invoice_number,
                    "company": inv.company,
                    "file": inv.file,
                    "file_url": self._file_url(inv.file),
                    "invoice_date": inv.invoice_date.strftime("%Y-%m-%d") if getattr(inv, "invoice_date", None) else None,
                    "added_date": inv.added_date.strftime("%Y-%m-%d %H:%M:%S") if inv.added_date else None,
                    "updated_date": inv.updated_date.strftime("%Y-%m-%d %H:%M:%S") if inv.updated_date else None,
                }
            }
        except Exception as e:
            return {"error": str(e)}

    def delete(self, id: int):
        try:
            inv = self.db.query(InvoiceModel).filter(InvoiceModel.id == id).first()
            if not inv:
                return "No data found"

            if inv.file:
                try:
                    FileClass(self.db).delete(inv.file)
                except Exception as e:
                    return {"status": "error", "message": f"Error al eliminar archivo: {str(e)}"}

            self.db.delete(inv)
            self.db.commit()
            return "success"
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

