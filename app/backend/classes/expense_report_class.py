from app.backend.db.models import ExpenseReportModel
from datetime import datetime
from sqlalchemy import func

class ExpenseReportClass:
    def __init__(self, db):
        self.db = db

    def get_all(self, page=0, items_per_page=10):
        try:
            base_query = self.db.query(ExpenseReportModel).order_by(ExpenseReportModel.id.desc())
            
            if page > 0:
                total_items = self.db.query(func.count(ExpenseReportModel.id)).scalar()
                total_pages = (total_items + items_per_page - 1) // items_per_page

                if page < 1 or (total_pages > 0 and page > total_pages):
                    return {"status": "error", "message": "Invalid page number"}

                data = base_query.offset((page - 1) * items_per_page).limit(items_per_page).all()

                if not data:
                    return {"status": "error", "message": "No data found"}

                serialized_data = [{
                    "id": expense_report.id,
                    "expense_type_id": expense_report.expense_type_id,
                    "document_number": expense_report.document_number,
                    "company": expense_report.company,
                    "amount": expense_report.amount,
                    "document_date": expense_report.document_date.strftime("%Y-%m-%d %H:%M:%S") if expense_report.document_date else None,
                    "file": expense_report.file,
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
                    "expense_type_id": expense_report.expense_type_id,
                    "document_number": expense_report.document_number,
                    "company": expense_report.company,
                    "amount": expense_report.amount,
                    "document_date": expense_report.document_date.strftime("%Y-%m-%d %H:%M:%S") if expense_report.document_date else None,
                    "file": expense_report.file,
                    "added_date": expense_report.added_date.strftime("%Y-%m-%d %H:%M:%S") if expense_report.added_date else None,
                    "updated_date": expense_report.updated_date.strftime("%Y-%m-%d %H:%M:%S") if expense_report.updated_date else None
                } for expense_report in data]

                return serialized_data

        except Exception as e:
            error_message = str(e)
            return {"status": "error", "message": error_message}
    
    def get_list(self):
        try:
            data = (
                self.db.query(ExpenseReportModel)
                .order_by(ExpenseReportModel.id.desc())
                .all()
            )

            serialized_data = [{
                    "id": expense_report.id,
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
    
    def update(self, id, form_data):
        existing_expense_report = self.db.query(ExpenseReportModel).filter(ExpenseReportModel.id == id).one_or_none()

        if not existing_expense_report:
            return "No data found"

        try:
            existing_expense_report.expense_type_id = form_data.expense_type_id
            existing_expense_report.document_number = form_data.document_number
            existing_expense_report.company = form_data.company
            existing_expense_report.amount = form_data.amount
            existing_expense_report.document_date = form_data.document_date
            existing_expense_report.file = form_data.file
            existing_expense_report.updated_date = datetime.utcnow()

            self.db.commit()
            self.db.refresh(existing_expense_report)
            return "Expense report updated successfully"
        except Exception as e:
            self.db.rollback()
            error_message = str(e)
            return {"status": "error", "message": error_message}
        
    def store(self, expense_report_inputs):
        try:
            new_expense_report = ExpenseReportModel(
                expense_type_id=expense_report_inputs.expense_type_id,
                document_number=expense_report_inputs.document_number,
                company=expense_report_inputs.company,
                amount=expense_report_inputs.amount,
                document_date=expense_report_inputs.document_date,
                file=expense_report_inputs.file,
                added_date=datetime.utcnow()
            )

            self.db.add(new_expense_report)
            self.db.commit()
            self.db.refresh(new_expense_report)

            return {
                "status": "Reporte de gasto registrado exitosamente.",
                "expense_report_id": new_expense_report.id
            }

        except Exception as e:
            self.db.rollback()
            return {"status": "error", "message": str(e)}

    def get(self, id):
        try:
            data_query = self.db.query(ExpenseReportModel).filter(ExpenseReportModel.id == id).first()

            if data_query:
                expense_report_data = {
                    "id": data_query.id,
                    "expense_type_id": data_query.expense_type_id,
                    "document_number": data_query.document_number,
                    "company": data_query.company,
                    "amount": data_query.amount,
                    "document_date": data_query.document_date.strftime("%Y-%m-%d %H:%M:%S") if data_query.document_date else None,
                    "file": data_query.file,
                    "added_date": data_query.added_date.strftime("%Y-%m-%d %H:%M:%S") if data_query.added_date else None,
                    "updated_date": data_query.updated_date.strftime("%Y-%m-%d %H:%M:%S") if data_query.updated_date else None
                }

                return {"expense_report_data": expense_report_data}

            else:
                return {"error": "No se encontraron datos para el campo especificado."}
            
        except Exception as e:
            return {"error": str(e)}
        
    def delete(self, id):
        try:
            data = self.db.query(ExpenseReportModel).filter(ExpenseReportModel.id == id).first()
            if data:
                self.db.delete(data)
                self.db.commit()
                return 'success'
            else:
                return "No data found"
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
