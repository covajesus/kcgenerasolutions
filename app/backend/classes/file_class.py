from pathlib import Path

from fastapi import HTTPException, UploadFile

class FileClass:
    def __init__(self, db):
        self.db = db

        # Guardar SIEMPRE dentro del proyecto actual.
        # Ej producción: /var/www/api.kcgeneralsolutions.ca/public_html/files
        self.base_dir = Path(__file__).resolve().parents[3] / "files"
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _safe_full_path(self, remote_path: str) -> Path:
        """
        Evita path traversal: remote_path debe quedarse dentro de base_dir.
        """
        rp = (remote_path or "").replace("\\", "/").lstrip("/")
        full_path = (self.base_dir / rp).resolve(strict=False)
        base = self.base_dir.resolve(strict=False)
        if base != full_path and base not in full_path.parents:
            raise HTTPException(status_code=400, detail="Ruta de archivo inválida")
        return full_path

    def upload(self, file: UploadFile, remote_path: str) -> str:
        try:
            full_path = self._safe_full_path(remote_path)
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Leer el contenido del archivo
            # Resetear la posición del stream al inicio si es necesario
            file.file.seek(0)
            content = file.file.read()
            file.file.seek(0)  # Resetear para posibles lecturas futuras
            
            with open(full_path, "wb") as f:
                f.write(content)
            return f"Archivo subido exitosamente a {remote_path}"
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al subir archivo: {str(e)}")

    def temporal_upload(self, file_content: bytes, remote_path: str) -> str:
        try:
            full_path = self._safe_full_path(remote_path)
            full_path.parent.mkdir(parents=True, exist_ok=True)
            with open(full_path, "wb") as f:
                f.write(file_content)
            return f"Archivo subido exitosamente a {remote_path}"
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al subir archivo: {str(e)}")

    def delete(self, remote_path: str) -> str:
        try:
            full_path = self._safe_full_path(remote_path)
            if full_path.exists():
                full_path.unlink()
                return "success"
            else:
                raise HTTPException(status_code=404, detail=f"Archivo no encontrado: {remote_path}")
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al eliminar archivo: {str(e)}")

    def download(self, remote_path: str) -> bytes:
        try:
            full_path = self._safe_full_path(remote_path)
            if full_path.exists():
                with open(full_path, "rb") as f:
                    return f.read()
            else:
                raise HTTPException(status_code=404, detail=f"Archivo no encontrado: {remote_path}")
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al descargar archivo: {str(e)}")

    def get(self, remote_path: str) -> str:
        try:
            # root_path del backend es /api
            rp = (remote_path or "").replace("\\", "/").lstrip("/")
            return f"/api/files/view/{rp}"
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al generar URL del archivo: {str(e)}")