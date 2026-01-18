from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path
import mimetypes

files = APIRouter(
    prefix="/files",
    tags=["files"]
)

BASE_DIR = Path(__file__).resolve().parents[3]
FILES_DIR = BASE_DIR / "files"
FILES_DIR.mkdir(parents=True, exist_ok=True)

def _safe_full_path(file_path: str) -> Path:
    rp = (file_path or "").replace("\\", "/").lstrip("/")
    full_path = (FILES_DIR / rp).resolve(strict=False)
    base = FILES_DIR.resolve(strict=False)
    if base != full_path and base not in full_path.parents:
        raise HTTPException(status_code=400, detail="Ruta de archivo inválida")
    return full_path

@files.get("/download/{file_path:path}")
def download_file(file_path: str):
    full_path = _safe_full_path(file_path)

    if not full_path.exists() or not full_path.is_file():
        raise HTTPException(status_code=404, detail="Archivo no encontrado")

    return FileResponse(
        path=full_path,
        filename=full_path.name,
        media_type="application/octet-stream",
        headers={"Content-Disposition": f"attachment; filename={full_path.name}"}
    )

@files.get("/view/{file_path:path}")
def view_file(file_path: str):
    """
    Devuelve el archivo inline (útil para <img src="...">).
    """
    full_path = _safe_full_path(file_path)

    if not full_path.exists() or not full_path.is_file():
        raise HTTPException(status_code=404, detail="Archivo no encontrado")

    media_type, _ = mimetypes.guess_type(str(full_path))
    return FileResponse(
        path=full_path,
        media_type=media_type or "application/octet-stream",
    )
