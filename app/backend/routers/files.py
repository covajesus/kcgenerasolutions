from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
import os
from pathlib import Path
import mimetypes

files = APIRouter(
    prefix="/files",
    tags=["files"]
)

FILES_DIR = "C:/Users/jesus/OneDrive/Escritorio/backend-lacasadelvitrificado/files"

@files.get("/download/{file_path:path}")
def download_file(file_path: str):
    full_path = Path(FILES_DIR) / file_path

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
    full_path = Path(FILES_DIR) / file_path

    if not full_path.exists() or not full_path.is_file():
        raise HTTPException(status_code=404, detail="Archivo no encontrado")

    media_type, _ = mimetypes.guess_type(str(full_path))
    return FileResponse(
        path=full_path,
        media_type=media_type or "application/octet-stream",
    )
