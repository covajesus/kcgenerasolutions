from app.backend.db.models import ExpenseReportModel, SupplierModel
from datetime import datetime
from sqlalchemy import func, cast, String, func as sa_func
from app.backend.classes.file_class import FileClass

class ExpenseReportClass:
    def __init__(self, db):
        self.db = db

    def _get_value(self, obj, key, default=None):
        if isinstance(obj, dict):
            return obj.get(key, default)
        return getattr(obj, key, default)

    def _is_admin(self, session_user) -> bool:
        return getattr(session_user, "rol_id", None) == 1

    def _apply_user_scope(self, query, session_user):
        """
        - rol_id == 1: ve todo
        - rol_id == 2 (u otros): filtra por user_id
        """
        if session_user is None:
            return query
        if self._is_admin(session_user):
            return query
        user_id = getattr(session_user, "id", None)
        # si no viene user_id en sesión, no devolver nada por seguridad
        if user_id is None:
            return query.filter(False)
        return query.filter(ExpenseReportModel.user_id == user_id)

    def _to_int_or_none(self, value):
        if value is None:
            return None
        try:
            return int(str(value).strip())
        except Exception:
            return None

    def _file_url(self, remote_path: str | None):
        if not remote_path:
            return None
        # root_path del backend es /api
        return f"/api/files/view/{remote_path}"

    def _ensure_supplier_from_company(self, company_value):
        """
        Cuando llega company en expense_report, guardar ese valor en la tabla suppliers.
        Solo crea si no existe (case-insensitive). No vincula por FK.
        """
        name = (str(company_value).strip() if company_value is not None else "")
        if not name:
            return

        exists = (
            self.db.query(SupplierModel.id)
            .filter(sa_func.lower(SupplierModel.supplier) == name.lower())
            .first()
        )
        if exists:
            return

        self.db.add(
            SupplierModel(
                supplier=name,
                added_date=datetime.utcnow(),
                updated_date=datetime.utcnow(),
            )
        )

    def get_all(self, page=0, session_user=None, items_per_page=10):
        try:
            base_query = self.db.query(ExpenseReportModel).order_by(ExpenseReportModel.id.desc())
            base_query = self._apply_user_scope(base_query, session_user)
            
            if page > 0:
                total_items = base_query.count()
                total_pages = (total_items + items_per_page - 1) // items_per_page

                if page < 1 or (total_pages > 0 and page > total_pages):
                    return {"status": "error", "message": "Invalid page number"}

                data = base_query.offset((page - 1) * items_per_page).limit(items_per_page).all()

                if not data:
                    return {"status": "error", "message": "No data found"}

                serialized_data = [{
                    "id": expense_report.id,
                    "user_id": expense_report.user_id,
                    "expense_type_id": expense_report.expense_type_id,
                    "document_number": expense_report.document_number,
                    "company": expense_report.company,
                    "amount": expense_report.amount,
                    "document_date": expense_report.document_date.strftime("%Y-%m-%d %H:%M:%S") if expense_report.document_date else None,
                    "file": expense_report.file,
                    "file_url": self._file_url(expense_report.file),
                    "added_date": expense_report.added_date.strftime("%Y-%m-%d %H:%M:%S") if expense_report.added_date else None,
                    "updated_date": expense_report.updated_date.strftime("%Y-%m-%d %H:%M:%S") if expense_report.updated_date else None
                } for expense_report in data]

                return {
                    "total_items": total_items,
                    "total_pages": total_pages,
                    "current_page": page,
                    "items_per_page": items_per_page,
                    "data": serialized_data
                }

            else:
                data = base_query.all()

                serialized_data = [{
                    "id": expense_report.id,
                    "user_id": expense_report.user_id,
                    "expense_type_id": expense_report.expense_type_id,
                    "document_number": expense_report.document_number,
                    "company": expense_report.company,
                    "amount": expense_report.amount,
                    "document_date": expense_report.document_date.strftime("%Y-%m-%d %H:%M:%S") if expense_report.document_date else None,
                    "file": expense_report.file,
                    "file_url": self._file_url(expense_report.file),
                    "added_date": expense_report.added_date.strftime("%Y-%m-%d %H:%M:%S") if expense_report.added_date else None,
                    "updated_date": expense_report.updated_date.strftime("%Y-%m-%d %H:%M:%S") if expense_report.updated_date else None
                } for expense_report in data]

                return serialized_data

        except Exception as e:
            error_message = str(e)
            return {"status": "error", "message": error_message}
    
    def get_list(self, session_user=None):
        try:
            query = self.db.query(ExpenseReportModel).order_by(ExpenseReportModel.id.desc())
            query = self._apply_user_scope(query, session_user)
            data = query.all()

            serialized_data = [{
                    "id": expense_report.id,
                    "user_id": expense_report.user_id,
                    "expense_type_id": expense_report.expense_type_id,
                    "document_number": expense_report.document_number,
                    "company": expense_report.company,
                    "amount": expense_report.amount
                } for expense_report in data]

            return {
                "data": serialized_data
            }

        except Exception as e:
            error_message = str(e)
            return {"status": "error", "message": error_message}

    def search(self, search_inputs, session_user=None, items_per_page=10):
        """
        Busca por company (o company_name) y/o document_number.
        Si envías ambos, aplica ambos filtros.
        """
        try:
            page = self._get_value(search_inputs, "page", 0) or 0
            company = self._get_value(search_inputs, "company") or self._get_value(search_inputs, "company_name")
            document_number = self._get_value(search_inputs, "document_number")

            if (company is None or str(company).strip() == "") and document_number is None:
                return {"status": "error", "message": "Debe enviar company y/o document_number"}

            query = self.db.query(ExpenseReportModel).order_by(ExpenseReportModel.id.desc())
            query = self._apply_user_scope(query, session_user)

            if company is not None and str(company).strip() != "":
                query = query.filter(ExpenseReportModel.company.ilike(f"%{str(company).strip()}%"))

            if document_number is not None and str(document_number).strip() != "":
                # document_number es INT en DB, pero permitimos buscar como string
                doc_str = str(document_number).strip()
                query = query.filter(cast(ExpenseReportModel.document_number, String).ilike(f"%{doc_str}%"))

            if page and page > 0:
                total_items = query.count()
                total_pages = (total_items + items_per_page - 1) // items_per_page

                if page < 1 or (total_pages > 0 and page > total_pages):
                    return {"status": "error", "message": "Invalid page number"}

                data = query.offset((page - 1) * items_per_page).limit(items_per_page).all()
                if not data:
                    return {"status": "error", "message": "No data found"}

                serialized_data = [{
                    "id": expense_report.id,
                    "user_id": expense_report.user_id,
                    "expense_type_id": expense_report.expense_type_id,
                    "document_number": expense_report.document_number,
                    "company": expense_report.company,
                    "amount": expense_report.amount,
                    "document_date": expense_report.document_date.strftime("%Y-%m-%d %H:%M:%S") if expense_report.document_date else None,
                    "file": expense_report.file,
                    "file_url": self._file_url(expense_report.file),
                    "added_date": expense_report.added_date.strftime("%Y-%m-%d %H:%M:%S") if expense_report.added_date else None,
                    "updated_date": expense_report.updated_date.strftime("%Y-%m-%d %H:%M:%S") if expense_report.updated_date else None
                } for expense_report in data]

                return {
                    "total_items": total_items,
                    "total_pages": total_pages,
                    "current_page": page,
                    "items_per_page": items_per_page,
                    "data": serialized_data
                }

            data = query.all()
            serialized_data = [{
                "id": expense_report.id,
                "user_id": expense_report.user_id,
                "expense_type_id": expense_report.expense_type_id,
                "document_number": expense_report.document_number,
                "company": expense_report.company,
                "amount": expense_report.amount,
                "document_date": expense_report.document_date.strftime("%Y-%m-%d %H:%M:%S") if expense_report.document_date else None,
                "file": expense_report.file,
                "file_url": self._file_url(expense_report.file),
                "added_date": expense_report.added_date.strftime("%Y-%m-%d %H:%M:%S") if expense_report.added_date else None,
                "updated_date": expense_report.updated_date.strftime("%Y-%m-%d %H:%M:%S") if expense_report.updated_date else None
            } for expense_report in data]

            return serialized_data

        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def update(self, id, form_data, session_user=None):
        q = self.db.query(ExpenseReportModel).filter(ExpenseReportModel.id == id)
        q = self._apply_user_scope(q, session_user)
        existing_expense_report = q.one_or_none()

        if not existing_expense_report:
            return "No data found"

        try:
            existing_expense_report.expense_type_id = self._get_value(form_data, "expense_type_id")
            existing_expense_report.document_number = self._to_int_or_none(self._get_value(form_data, "document_number"))
            existing_expense_report.company = self._get_value(form_data, "company")
            # Guardar company en la tabla suppliers (si no existe)
            self._ensure_supplier_from_company(existing_expense_report.company)
            existing_expense_report.amount = self._get_value(form_data, "amount")
            existing_expense_report.document_date = self._get_value(form_data, "document_date")

            # Solo actualizar archivo si viene en el payload
            if isinstance(form_data, dict) and "file" in form_data and form_data.get("file") is not None:
                existing_expense_report.file = form_data.get("file")
            existing_expense_report.updated_date = datetime.utcnow()

            self.db.commit()
            self.db.refresh(existing_expense_report)
            return {
                "status": "Expense report updated successfully",
                "expense_report_id": existing_expense_report.id,
                "file": existing_expense_report.file,
                "file_url": self._file_url(existing_expense_report.file),
            }
        except Exception as e:
            self.db.rollback()
            error_message = str(e)
            return {"status": "error", "message": error_message}
        
    def store(self, expense_report_inputs):
        try:
            user_id = self._get_value(expense_report_inputs, "user_id")
            if user_id is None:
                return {"status": "error", "message": "user_id es requerido"}

            company_value = self._get_value(expense_report_inputs, "company")
            # Guardar company en la tabla suppliers (si no existe)
            self._ensure_supplier_from_company(company_value)

            new_expense_report = ExpenseReportModel(
                user_id=user_id,
                expense_type_id=self._get_value(expense_report_inputs, "expense_type_id"),
                document_number=self._to_int_or_none(self._get_value(expense_report_inputs, "document_number")),
                company=company_value,
                amount=self._get_value(expense_report_inputs, "amount"),
                document_date=self._get_value(expense_report_inputs, "document_date"),
                file=self._get_value(expense_report_inputs, "file"),
                added_date=datetime.utcnow(),
                updated_date=datetime.utcnow(),
            )

            self.db.add(new_expense_report)
            self.db.commit()
            self.db.refresh(new_expense_report)

            return {
                "status": "Reporte de gasto registrado exitosamente.",
                "expense_report_id": new_expense_report.id,
                "file": new_expense_report.file,
                "file_url": self._file_url(new_expense_report.file),
            }

        except Exception as e:
            self.db.rollback()
            return {"status": "error", "message": str(e)}

    def get(self, id, session_user=None):
        try:
            q = self.db.query(ExpenseReportModel).filter(ExpenseReportModel.id == id)
            q = self._apply_user_scope(q, session_user)
            data_query = q.first()

            if data_query:
                expense_report_data = {
                    "id": data_query.id,
                    "user_id": data_query.user_id,
                    "expense_type_id": data_query.expense_type_id,
                    "document_number": data_query.document_number,
                    "company": data_query.company,
                    "amount": data_query.amount,
                    "document_date": data_query.document_date.strftime("%Y-%m-%d %H:%M:%S") if data_query.document_date else None,
                    "file": data_query.file,
                    "file_url": self._file_url(data_query.file),
                    "added_date": data_query.added_date.strftime("%Y-%m-%d %H:%M:%S") if data_query.added_date else None,
                    "updated_date": data_query.updated_date.strftime("%Y-%m-%d %H:%M:%S") if data_query.updated_date else None
                }

                return {"expense_report_data": expense_report_data}

            else:
                return {"error": "No se encontraron datos para el campo especificado."}
            
        except Exception as e:
            return {"error": str(e)}
        
    def delete(self, id, session_user=None):
        try:
            q = self.db.query(ExpenseReportModel).filter(ExpenseReportModel.id == id)
            q = self._apply_user_scope(q, session_user)
            data = q.first()
            if data:
                # Si tiene archivo asociado, borrarlo primero. Si falla, NO borrar el registro.
                if data.file:
                    try:
                        FileClass(self.db).delete(data.file)
                    except Exception as e:
                        return {"status": "error", "message": f"Error al eliminar archivo: {str(e)}"}

                self.db.delete(data)
                self.db.commit()
                return 'success'
            else:
                return "No data found"
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
