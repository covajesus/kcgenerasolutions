from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from fastapi.responses import FileResponse
from app.backend.db.database import get_db
from sqlalchemy.orm import Session
from app.backend.schemas import UserLogin, StoreExpenseReport, ExpenseReportList, UpdateExpenseReport, ExpenseReportSearch
from app.backend.classes.expense_report_class import ExpenseReportClass
from app.backend.auth.auth_user import get_current_active_user
from app.backend.classes.file_class import FileClass
from app.backend.db.models import ExpenseReportModel
from datetime import datetime
from pathlib import Path
import mimetypes
import uuid

expense_reports = APIRouter(
    prefix="/expense_reports",
    tags=["Expense Reports"]
)

BASE_DIR = Path(__file__).resolve().parents[3]
FILES_DIR = BASE_DIR / "files"


def _safe_full_path(file_path: str) -> Path:
    rp = (file_path or "").replace("\\", "/").lstrip("/")
    full_path = (FILES_DIR / rp).resolve(strict=False)
    base = FILES_DIR.resolve(strict=False)
    if base != full_path and base not in full_path.parents:
        raise HTTPException(status_code=400, detail="Ruta de archivo inválida")
    return full_path

@expense_reports.post("/")
def index(expense_report_inputs: ExpenseReportList, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = ExpenseReportClass(db).get_all(expense_report_inputs.page, session_user=session_user)

    return {"message": data}

@expense_reports.get("/list")
def list_all(session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = ExpenseReportClass(db).get_list(session_user=session_user)

    return {"message": data}

@expense_reports.post("/search")
def search(
    search_inputs: ExpenseReportSearch,
    session_user: UserLogin = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    data = ExpenseReportClass(db).search(search_inputs, session_user=session_user)
    return {"message": data}

@expense_reports.post("/store")
def store(
    form_data: StoreExpenseReport = Depends(StoreExpenseReport.as_form),
    file: UploadFile = File(None),
    session_user: UserLogin = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    payload = form_data.model_dump()
    # Guardar user_id desde la sesión (no confiar en lo que mande el cliente)
    payload["user_id"] = getattr(session_user, "id", None)

    if file is not None:
        timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        unique_id = uuid.uuid4().hex[:8]
        extension = file.filename.rsplit('.', 1)[-1].lower() if file.filename and '.' in file.filename else ''
        filename = f"expense_{timestamp}_{unique_id}"
        remote_path = f"expense_reports/{filename}.{extension}" if extension else f"expense_reports/{filename}"

        FileClass(db).upload(file, remote_path)
        payload["file"] = remote_path

    data = ExpenseReportClass(db).store(payload)

    return {"message": data}

@expense_reports.post("/update/{id}")
def update(
    id: int,
    form_data: UpdateExpenseReport = Depends(UpdateExpenseReport.as_form),
    file: UploadFile = File(None),
    session_user: UserLogin = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    payload = form_data.model_dump()

    if file is not None:
        # Guardar path actual para borrarlo después de un update exitoso
        old_remote_path = None
        existing = db.query(ExpenseReportModel).filter(ExpenseReportModel.id == id).first()
        if existing and existing.file:
            old_remote_path = existing.file

        timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        unique_id = uuid.uuid4().hex[:8]
        extension = file.filename.rsplit('.', 1)[-1].lower() if file.filename and '.' in file.filename else ''
        filename = f"expense_{timestamp}_{unique_id}"
        remote_path = f"expense_reports/{filename}.{extension}" if extension else f"expense_reports/{filename}"

        FileClass(db).upload(file, remote_path)
        payload["file"] = remote_path

    data = ExpenseReportClass(db).update(id, payload, session_user=session_user)

    # Si llegó archivo nuevo y el update fue exitoso, borrar el anterior
    if file is not None and isinstance(data, dict) and data.get("status") != "error":
        try:
            if old_remote_path and old_remote_path != payload.get("file"):
                FileClass(db).delete(old_remote_path)
        except Exception:
            # No romper el update si el archivo viejo no existe o falla el delete
            pass

    return {"message": data}

@expense_reports.delete("/delete/{id}")
def delete(id: int, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = ExpenseReportClass(db).delete(id, session_user=session_user)

    return {"message": data}

@expense_reports.get("/edit/{id}")
def edit(id: int, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = ExpenseReportClass(db).get(id, session_user=session_user)

    return {"message": data}


@expense_reports.get("/download/{id}")
def download(id: int, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    r = db.query(ExpenseReportModel).filter(ExpenseReportModel.id == id).first()
    if not r or not r.file:
        raise HTTPException(status_code=404, detail="Archivo no encontrado")

    full_path = _safe_full_path(r.file)
    if not full_path.exists() or not full_path.is_file():
        raise HTTPException(status_code=404, detail="Archivo no encontrado")

    media_type, _ = mimetypes.guess_type(str(full_path))
    return FileResponse(
        path=full_path,
        filename=full_path.name,
        media_type=media_type or "application/octet-stream",
        headers={"Content-Disposition": f"attachment; filename={full_path.name}"},
    )
