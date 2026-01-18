from datetime import datetime
import uuid

from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path
import mimetypes
from sqlalchemy.orm import Session

from app.backend.auth.auth_user import get_current_active_user
from app.backend.classes.budget_class import BudgetClass
from app.backend.classes.file_class import FileClass
from app.backend.db.database import get_db
from app.backend.db.models import BudgetModel
from app.backend.schemas import UserLogin, BudgetList, BudgetSearch, StoreBudget, UpdateBudget


budgets = APIRouter(
    prefix="/budgets",
    tags=["Budgets"]
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

@budgets.post("/")
def index(inputs: BudgetList, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = BudgetClass(db).get_all(inputs.page)
    return {"message": data}


@budgets.get("/list")
def list_all(session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = BudgetClass(db).get_list()
    return {"message": data}

@budgets.post("/search")
def search(inputs: BudgetSearch, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = BudgetClass(db).search(inputs.model_dump())
    return {"message": data}


@budgets.post("/store")
def store(
    form_data: StoreBudget = Depends(StoreBudget.as_form),
    file: UploadFile = File(None),
    uploaded_file: UploadFile = File(None),
    session_user: UserLogin = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    payload = form_data.model_dump()

    f = file or uploaded_file
    if f is not None:
        timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        unique_id = uuid.uuid4().hex[:8]
        extension = f.filename.rsplit('.', 1)[-1].lower() if f.filename and '.' in f.filename else ''
        filename = f"budget_{timestamp}_{unique_id}"
        remote_path = f"budgets/{filename}.{extension}" if extension else f"budgets/{filename}"
        FileClass(db).upload(f, remote_path)
        payload["file"] = remote_path

    data = BudgetClass(db).store(payload)
    return {"message": data}


@budgets.post("/update/{id}")
def update(
    id: int,
    form_data: UpdateBudget = Depends(UpdateBudget.as_form),
    file: UploadFile = File(None),
    uploaded_file: UploadFile = File(None),
    session_user: UserLogin = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    payload = form_data.model_dump()

    old_remote_path = None
    f = file or uploaded_file
    if f is not None:
        existing = db.query(BudgetModel).filter(BudgetModel.id == id).first()
        if existing and existing.file:
            old_remote_path = existing.file

        timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        unique_id = uuid.uuid4().hex[:8]
        extension = f.filename.rsplit('.', 1)[-1].lower() if f.filename and '.' in f.filename else ''
        filename = f"budget_{timestamp}_{unique_id}"
        remote_path = f"budgets/{filename}.{extension}" if extension else f"budgets/{filename}"
        FileClass(db).upload(f, remote_path)
        payload["file"] = remote_path

    data = BudgetClass(db).update(id, payload)

    # Borrar archivo viejo si el update fue exitoso
    if f is not None and isinstance(data, dict) and data.get("status") != "error":
        try:
            if old_remote_path and old_remote_path != payload.get("file"):
                FileClass(db).delete(old_remote_path)
        except Exception:
            pass

    return {"message": data}


@budgets.delete("/delete/{id}")
def delete(id: int, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = BudgetClass(db).delete(id)
    return {"message": data}


@budgets.get("/edit/{id}")
def edit(id: int, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = BudgetClass(db).get(id)
    return {"message": data}


@budgets.get("/download/{id}")
def download(id: int, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    b = db.query(BudgetModel).filter(BudgetModel.id == id).first()
    if not b or not b.file:
        raise HTTPException(status_code=404, detail="Archivo no encontrado")

    full_path = _safe_full_path(b.file)
    if not full_path.exists() or not full_path.is_file():
        raise HTTPException(status_code=404, detail="Archivo no encontrado")

    media_type, _ = mimetypes.guess_type(str(full_path))
    return FileResponse(
        path=full_path,
        filename=full_path.name,
        media_type=media_type or "application/octet-stream",
        headers={"Content-Disposition": f"attachment; filename={full_path.name}"},
    )

