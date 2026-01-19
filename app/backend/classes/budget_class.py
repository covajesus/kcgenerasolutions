import os
import platform
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import func

from app.backend.classes.file_class import FileClass
from app.backend.db.models import BudgetModel


class BudgetClass:
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
            base_query = self.db.query(BudgetModel).order_by(BudgetModel.id.desc())

            if page > 0:
                total_items = self.db.query(func.count(BudgetModel.id)).scalar()
                total_pages = (total_items + items_per_page - 1) // items_per_page

                if page < 1 or (total_pages > 0 and page > total_pages):
                    return {"status": "error", "message": "Invalid page number"}

                data = base_query.offset((page - 1) * items_per_page).limit(items_per_page).all()

                if not data:
                    return {"status": "error", "message": "No data found"}

                serialized_data = [{
                    "id": b.id,
                    "budget_number": b.budget_number,
                    "company": b.company,
                    "amount": getattr(b, "amount", None),
                    "file": b.file,
                    "file_url": self._file_url(b.file),
                    "budget_date": b.budget_date.strftime("%Y-%m-%d") if getattr(b, "budget_date", None) else None,
                    "added_date": b.added_date.strftime("%Y-%m-%d %H:%M:%S") if b.added_date else None,
                    "updated_date": b.updated_date.strftime("%Y-%m-%d %H:%M:%S") if b.updated_date else None,
                } for b in data]

                return {
                    "total_items": total_items,
                    "total_pages": total_pages,
                    "current_page": page,
                    "items_per_page": items_per_page,
                    "data": serialized_data
                }

            data = base_query.all()
            return [{
                "id": b.id,
                "budget_number": b.budget_number,
                "company": b.company,
                "amount": getattr(b, "amount", None),
                "file": b.file,
                "file_url": self._file_url(b.file),
                "budget_date": b.budget_date.strftime("%Y-%m-%d") if getattr(b, "budget_date", None) else None,
                "added_date": b.added_date.strftime("%Y-%m-%d %H:%M:%S") if b.added_date else None,
                "updated_date": b.updated_date.strftime("%Y-%m-%d %H:%M:%S") if b.updated_date else None,
            } for b in data]

        except Exception as e:
            return {"status": "error", "message": str(e)}

    def get_list(self):
        try:
            data = self.db.query(BudgetModel).order_by(BudgetModel.id.desc()).all()
            return {
                "data": [{
                    "id": b.id,
                    "budget_number": b.budget_number,
                    "company": b.company,
                    "amount": getattr(b, "amount", None),
                    "budget_date": b.budget_date.strftime("%Y-%m-%d") if getattr(b, "budget_date", None) else None,
                } for b in data]
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def search(self, search_inputs, items_per_page=10):
        """
        Busca por budget_number (parcial).
        """
        try:
            page = (search_inputs or {}).get("page", 0) or 0
            budget_number = (search_inputs or {}).get("budget_number")

            if budget_number is None or str(budget_number).strip() == "":
                return {"status": "error", "message": "Debe enviar budget_number"}

            q = self.db.query(BudgetModel).order_by(BudgetModel.id.desc())
            q = q.filter(BudgetModel.budget_number.ilike(f"%{str(budget_number).strip()}%"))

            if page and page > 0:
                total_items = q.count()
                total_pages = (total_items + items_per_page - 1) // items_per_page

                if page < 1 or (total_pages > 0 and page > total_pages):
                    return {"status": "error", "message": "Invalid page number"}

                data = q.offset((page - 1) * items_per_page).limit(items_per_page).all()
                if not data:
                    return {"status": "error", "message": "No data found"}

                serialized_data = [{
                    "id": b.id,
                    "budget_number": b.budget_number,
                    "company": b.company,
                    "amount": getattr(b, "amount", None),
                    "file": b.file,
                    "file_url": self._file_url(b.file),
                    "budget_date": b.budget_date.strftime("%Y-%m-%d") if getattr(b, "budget_date", None) else None,
                    "added_date": b.added_date.strftime("%Y-%m-%d %H:%M:%S") if b.added_date else None,
                    "updated_date": b.updated_date.strftime("%Y-%m-%d %H:%M:%S") if b.updated_date else None,
                } for b in data]

                return {
                    "total_items": total_items,
                    "total_pages": total_pages,
                    "current_page": page,
                    "items_per_page": items_per_page,
                    "data": serialized_data
                }

            data = q.all()
            return [{
                "id": b.id,
                "budget_number": b.budget_number,
                "company": b.company,
                "amount": getattr(b, "amount", None),
                "file": b.file,
                "file_url": self._file_url(b.file),
                "budget_date": b.budget_date.strftime("%Y-%m-%d") if getattr(b, "budget_date", None) else None,
                "added_date": b.added_date.strftime("%Y-%m-%d %H:%M:%S") if b.added_date else None,
                "updated_date": b.updated_date.strftime("%Y-%m-%d %H:%M:%S") if b.updated_date else None,
            } for b in data]

        except Exception as e:
            return {"status": "error", "message": str(e)}

    def store(self, payload: dict):
        try:
            b = BudgetModel(
                budget_number=str(payload.get("budget_number") or ""),
                company=str(payload.get("company") or ""),
                amount=str(payload.get("amount") or ""),
                file=payload.get("file"),
                budget_date=payload.get("budget_date"),
                added_date=datetime.utcnow(),
                updated_date=datetime.utcnow(),
            )
            self.db.add(b)
            self.db.commit()
            self.db.refresh(b)
            return {
                "status": "Presupuesto registrado exitosamente.",
                "budget_id": b.id,
                "file": b.file,
                "file_url": self._file_url(b.file),
                "budget_date": b.budget_date.strftime("%Y-%m-%d") if getattr(b, "budget_date", None) else None,
                "amount": getattr(b, "amount", None),
            }
        except Exception as e:
            self.db.rollback()
            return {"status": "error", "message": str(e)}

    def update(self, id: int, payload: dict):
        b = self.db.query(BudgetModel).filter(BudgetModel.id == id).one_or_none()
        if not b:
            return "No data found"

        try:
            b.budget_number = str(payload.get("budget_number") or "")
            b.company = str(payload.get("company") or "")
            b.amount = str(payload.get("amount") or "")
            if isinstance(payload, dict) and "file" in payload and payload.get("file") is not None:
                b.file = payload.get("file")
            if isinstance(payload, dict) and "budget_date" in payload:
                b.budget_date = payload.get("budget_date")
            b.updated_date = datetime.utcnow()
            self.db.commit()
            self.db.refresh(b)
            return {
                "status": "Budget updated successfully",
                "budget_id": b.id,
                "file": b.file,
                "file_url": self._file_url(b.file),
                "budget_date": b.budget_date.strftime("%Y-%m-%d") if getattr(b, "budget_date", None) else None,
                "amount": getattr(b, "amount", None),
            }
        except Exception as e:
            self.db.rollback()
            return {"status": "error", "message": str(e)}

    def get(self, id: int):
        try:
            b = self.db.query(BudgetModel).filter(BudgetModel.id == id).first()
            if not b:
                return {"error": "No se encontraron datos para el campo especificado."}
            return {
                "budget_data": {
                    "id": b.id,
                    "budget_number": b.budget_number,
                    "company": b.company,
                    "amount": getattr(b, "amount", None),
                    "file": b.file,
                    "file_url": self._file_url(b.file),
                    "budget_date": b.budget_date.strftime("%Y-%m-%d") if getattr(b, "budget_date", None) else None,
                    "added_date": b.added_date.strftime("%Y-%m-%d %H:%M:%S") if b.added_date else None,
                    "updated_date": b.updated_date.strftime("%Y-%m-%d %H:%M:%S") if b.updated_date else None,
                }
            }
        except Exception as e:
            return {"error": str(e)}

    def delete(self, id: int):
        try:
            b = self.db.query(BudgetModel).filter(BudgetModel.id == id).first()
            if not b:
                return "No data found"

            if b.file:
                try:
                    FileClass(self.db).delete(b.file)
                except Exception as e:
                    return {"status": "error", "message": f"Error al eliminar archivo: {str(e)}"}

            self.db.delete(b)
            self.db.commit()
            return "success"
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

