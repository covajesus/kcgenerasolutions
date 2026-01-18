from app.backend.db.models import ExpenseTypeModel
from datetime import datetime
from sqlalchemy import func

class ExpenseTypeClass:
    def __init__(self, db):
        self.db = db

    def get_all(self, page=0, items_per_page=10):
        try:
            base_query = self.db.query(ExpenseTypeModel).order_by(ExpenseTypeModel.id.desc())
            
            if page > 0:
                total_items = self.db.query(func.count(ExpenseTypeModel.id)).scalar()
                total_pages = (total_items + items_per_page - 1) // items_per_page

                if page < 1 or (total_pages > 0 and page > total_pages):
                    return {"status": "error", "message": "Invalid page number"}

                data = base_query.offset((page - 1) * items_per_page).limit(items_per_page).all()

                if not data:
                    return {"status": "error", "message": "No data found"}

                serialized_data = [{
                    "id": expense_type.id,
                    "expense_type": expense_type.expense_type,
                    "added_date": expense_type.added_date.strftime("%Y-%m-%d %H:%M:%S") if expense_type.added_date else None,
                    "updated_date": expense_type.updated_date.strftime("%Y-%m-%d %H:%M:%S") if expense_type.updated_date else None
                } for expense_type in data]

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
                    "id": expense_type.id,
                    "expense_type": expense_type.expense_type,
                    "added_date": expense_type.added_date.strftime("%Y-%m-%d %H:%M:%S") if expense_type.added_date else None,
                    "updated_date": expense_type.updated_date.strftime("%Y-%m-%d %H:%M:%S") if expense_type.updated_date else None
                } for expense_type in data]

                return serialized_data

        except Exception as e:
            error_message = str(e)
            return {"status": "error", "message": error_message}
    
    def get_list(self):
        try:
            data = (
                self.db.query(ExpenseTypeModel)
                .order_by(ExpenseTypeModel.expense_type)
                .all()
            )

            serialized_data = [{
                    "id": expense_type.id,
                    "expense_type": expense_type.expense_type
                } for expense_type in data]

            return {
                "data": serialized_data
            }

        except Exception as e:
            error_message = str(e)
            return {"status": "error", "message": error_message}
    
    def update(self, id, form_data):
        existing_expense_type = self.db.query(ExpenseTypeModel).filter(ExpenseTypeModel.id == id).one_or_none()

        if not existing_expense_type:
            return "No data found"

        try:
            existing_expense_type.expense_type = form_data.expense_type
            existing_expense_type.updated_date = datetime.utcnow()

            self.db.commit()
            self.db.refresh(existing_expense_type)
            return "Expense type updated successfully"
        except Exception as e:
            self.db.rollback()
            error_message = str(e)
            return {"status": "error", "message": error_message}
        
    def store(self, expense_type_inputs):
        try:
            new_expense_type = ExpenseTypeModel(
                expense_type=expense_type_inputs.expense_type,
                added_date=datetime.utcnow()
            )

            self.db.add(new_expense_type)
            self.db.commit()
            self.db.refresh(new_expense_type)

            return {
                "status": "Tipo de gasto registrado exitosamente.",
                "expense_type_id": new_expense_type.id
            }

        except Exception as e:
            self.db.rollback()
            return {"status": "error", "message": str(e)}

    def get(self, id):
        try:
            data_query = self.db.query(ExpenseTypeModel).filter(ExpenseTypeModel.id == id).first()

            if data_query:
                expense_type_data = {
                    "id": data_query.id,
                    "expense_type": data_query.expense_type,
                    "added_date": data_query.added_date.strftime("%Y-%m-%d %H:%M:%S") if data_query.added_date else None,
                    "updated_date": data_query.updated_date.strftime("%Y-%m-%d %H:%M:%S") if data_query.updated_date else None
                }

                return {"expense_type_data": expense_type_data}

            else:
                return {"error": "No se encontraron datos para el campo especificado."}
            
        except Exception as e:
            return {"error": str(e)}
        
    def delete(self, id):
        try:
            data = self.db.query(ExpenseTypeModel).filter(ExpenseTypeModel.id == id).first()
            if data:
                self.db.delete(data)
                self.db.commit()
                return 'success'
            else:
                return "No data found"
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
