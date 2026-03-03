import os
import platform
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import func

from app.backend.classes.file_class import FileClass
from app.backend.db.models import TaxReturnModel


class TaxReturnClass:
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
            base_query = self.db.query(TaxReturnModel).order_by(TaxReturnModel.id.desc())

            if page > 0:
                total_items = self.db.query(func.count(TaxReturnModel.id)).scalar()
                total_pages = (total_items + items_per_page - 1) // items_per_page

                if page < 1 or (total_pages > 0 and page > total_pages):
                    return {"status": "error", "message": "Invalid page number"}

                data = base_query.offset((page - 1) * items_per_page).limit(items_per_page).all()

                if not data:
                    return {"status": "error", "message": "No data found"}

                serialized_data = [{
                    "id": r.id,
                    "period": r.period,
                    "amount": getattr(r, "amount", None),
                    "file": r.file,
                    "file_url": self._file_url(r.file),
                    "added_date": r.added_date.strftime("%Y-%m-%d %H:%M:%S") if r.added_date else None,
                    "updated_date": r.updated_date.strftime("%Y-%m-%d %H:%M:%S") if r.updated_date else None,
                } for r in data]

                return {
                    "total_items": total_items,
                    "total_pages": total_pages,
                    "current_page": page,
                    "items_per_page": items_per_page,
                    "data": serialized_data
                }

            data = base_query.all()
            return [{
                "id": r.id,
                "period": r.period,
                "amount": getattr(r, "amount", None),
                "file": r.file,
                "file_url": self._file_url(r.file),
                "added_date": r.added_date.strftime("%Y-%m-%d %H:%M:%S") if r.added_date else None,
                "updated_date": r.updated_date.strftime("%Y-%m-%d %H:%M:%S") if r.updated_date else None,
            } for r in data]

        except Exception as e:
            return {"status": "error", "message": str(e)}

    def get_list(self):
        try:
            data = self.db.query(TaxReturnModel).order_by(TaxReturnModel.id.desc()).all()
            return {
                "data": [{
                    "id": r.id,
                    "period": r.period,
                    "amount": getattr(r, "amount", None),
                } for r in data]
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def search(self, search_inputs, items_per_page=10):
        try:
            page = (search_inputs or {}).get("page", 0) or 0
            period = (search_inputs or {}).get("period")

            if period is None or str(period).strip() == "":
                return {"status": "error", "message": "Debe enviar period"}

            q = self.db.query(TaxReturnModel).order_by(TaxReturnModel.id.desc())
            q = q.filter(TaxReturnModel.period.ilike(f"%{str(period).strip()}%"))

            if page and page > 0:
                total_items = q.count()
                total_pages = (total_items + items_per_page - 1) // items_per_page

                if page < 1 or (total_pages > 0 and page > total_pages):
                    return {"status": "error", "message": "Invalid page number"}

                data = q.offset((page - 1) * items_per_page).limit(items_per_page).all()
                if not data:
                    return {"status": "error", "message": "No data found"}

                serialized_data = [{
                    "id": r.id,
                    "period": r.period,
                    "amount": getattr(r, "amount", None),
                    "file": r.file,
                    "file_url": self._file_url(r.file),
                    "added_date": r.added_date.strftime("%Y-%m-%d %H:%M:%S") if r.added_date else None,
                    "updated_date": r.updated_date.strftime("%Y-%m-%d %H:%M:%S") if r.updated_date else None,
                } for r in data]

                return {
                    "total_items": total_items,
                    "total_pages": total_pages,
                    "current_page": page,
                    "items_per_page": items_per_page,
                    "data": serialized_data
                }

            data = q.all()
            return [{
                "id": r.id,
                "period": r.period,
                "amount": getattr(r, "amount", None),
                "file": r.file,
                "file_url": self._file_url(r.file),
                "added_date": r.added_date.strftime("%Y-%m-%d %H:%M:%S") if r.added_date else None,
                "updated_date": r.updated_date.strftime("%Y-%m-%d %H:%M:%S") if r.updated_date else None,
            } for r in data]

        except Exception as e:
            return {"status": "error", "message": str(e)}

    def store(self, payload: dict):
        try:
            r = TaxReturnModel(
                period=str(payload.get("period") or ""),
                amount=str(payload.get("amount") or ""),
                file=payload.get("file"),
                added_date=datetime.utcnow(),
                updated_date=datetime.utcnow(),
            )
            self.db.add(r)
            self.db.commit()
            self.db.refresh(r)
            return {
                "status": "Declaración de impuestos registrada exitosamente.",
                "tax_return_id": r.id,
                "file": r.file,
                "file_url": self._file_url(r.file),
                "period": r.period,
                "amount": getattr(r, "amount", None),
            }
        except Exception as e:
            self.db.rollback()
            return {"status": "error", "message": str(e)}

    def update(self, id: int, payload: dict):
        r = self.db.query(TaxReturnModel).filter(TaxReturnModel.id == id).one_or_none()
        if not r:
            return "No data found"

        try:
            r.period = str(payload.get("period") or "")
            r.amount = str(payload.get("amount") or "")
            if isinstance(payload, dict) and "file" in payload and payload.get("file") is not None:
                r.file = payload.get("file")
            r.updated_date = datetime.utcnow()
            self.db.commit()
            self.db.refresh(r)
            return {
                "status": "Declaración de impuestos actualizada exitosamente",
                "tax_return_id": r.id,
                "file": r.file,
                "file_url": self._file_url(r.file),
                "period": r.period,
                "amount": getattr(r, "amount", None),
            }
        except Exception as e:
            self.db.rollback()
            return {"status": "error", "message": str(e)}

    def get(self, id: int):
        try:
            r = self.db.query(TaxReturnModel).filter(TaxReturnModel.id == id).first()
            if not r:
                return {"error": "No se encontraron datos para el campo especificado."}
            return {
                "tax_return_data": {
                    "id": r.id,
                    "period": r.period,
                    "amount": getattr(r, "amount", None),
                    "file": r.file,
                    "file_url": self._file_url(r.file),
                    "added_date": r.added_date.strftime("%Y-%m-%d %H:%M:%S") if r.added_date else None,
                    "updated_date": r.updated_date.strftime("%Y-%m-%d %H:%M:%S") if r.updated_date else None,
                }
            }
        except Exception as e:
            return {"error": str(e)}

    def delete(self, id: int):
        try:
            r = self.db.query(TaxReturnModel).filter(TaxReturnModel.id == id).first()
            if not r:
                return "No data found"

            if r.file:
                try:
                    FileClass(self.db).delete(r.file)
                except Exception as e:
                    return {"status": "error", "message": f"Error al eliminar archivo: {str(e)}"}

            self.db.delete(r)
            self.db.commit()
            return "success"
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
