from datetime import datetime
import uuid

from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path
import mimetypes
from sqlalchemy.orm import Session

from app.backend.auth.auth_user import get_current_active_user
from app.backend.classes.tax_return_class import TaxReturnClass
from app.backend.classes.file_class import FileClass
from app.backend.db.database import get_db
from app.backend.db.models import TaxReturnModel
from app.backend.schemas import UserLogin, TaxReturnList, TaxReturnSearch, StoreTaxReturn, UpdateTaxReturn


tax_returns = APIRouter(
    prefix="/tax-returns",
    tags=["Tax Returns"]
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


@tax_returns.post("/")
def index(inputs: TaxReturnList, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = TaxReturnClass(db).get_all(inputs.page)
    return {"message": data}


@tax_returns.get("/list")
def list_all(session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = TaxReturnClass(db).get_list()
    return {"message": data}


@tax_returns.post("/search")
def search(inputs: TaxReturnSearch, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = TaxReturnClass(db).search(inputs.model_dump())
    return {"message": data}


@tax_returns.post("/store")
def store(
    form_data: StoreTaxReturn = Depends(StoreTaxReturn.as_form),
    file: UploadFile = File(...),
    session_user: UserLogin = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    payload = form_data.model_dump()

    timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
    unique_id = uuid.uuid4().hex[:8]
    extension = file.filename.rsplit('.', 1)[-1].lower() if file.filename and '.' in file.filename else ''
    filename = f"tax_return_{timestamp}_{unique_id}"
    remote_path = f"tax_returns/{filename}.{extension}" if extension else f"tax_returns/{filename}"
    FileClass(db).upload(file, remote_path)
    payload["file"] = remote_path

    data = TaxReturnClass(db).store(payload)
    return {"message": data}


@tax_returns.post("/update/{id}")
def update(
    id: int,
    form_data: UpdateTaxReturn = Depends(UpdateTaxReturn.as_form),
    file: UploadFile = File(None),
    session_user: UserLogin = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    payload = form_data.model_dump()
    old_remote_path = None

    if file is not None:
        existing = db.query(TaxReturnModel).filter(TaxReturnModel.id == id).first()
        if existing and existing.file:
            old_remote_path = existing.file

        timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        unique_id = uuid.uuid4().hex[:8]
        extension = file.filename.rsplit('.', 1)[-1].lower() if file.filename and '.' in file.filename else ''
        filename = f"tax_return_{timestamp}_{unique_id}"
        remote_path = f"tax_returns/{filename}.{extension}" if extension else f"tax_returns/{filename}"
        FileClass(db).upload(file, remote_path)
        payload["file"] = remote_path

    data = TaxReturnClass(db).update(id, payload)

    if file is not None and isinstance(data, dict) and data.get("status") != "error":
        try:
            if old_remote_path and old_remote_path != payload.get("file"):
                FileClass(db).delete(old_remote_path)
        except Exception:
            pass

    return {"message": data}


@tax_returns.delete("/delete/{id}")
def delete(id: int, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = TaxReturnClass(db).delete(id)
    return {"message": data}


@tax_returns.get("/edit/{id}")
def edit(id: int, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = TaxReturnClass(db).get(id)
    return {"message": data}


@tax_returns.get("/download/{id}")
def download(id: int, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    r = db.query(TaxReturnModel).filter(TaxReturnModel.id == id).first()
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
