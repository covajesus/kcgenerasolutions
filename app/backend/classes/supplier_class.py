from app.backend.db.models import SupplierModel
from datetime import datetime
from fastapi import HTTPException

class SupplierClass:
    def __init__(self, db):
        self.db = db

    def search(self, supplier_name: str):
        try:
            name = (supplier_name or "").strip()
            if not name:
                return {"status": "error", "message": "Debe enviar supplier_name"}

            data = (
                self.db.query(SupplierModel)
                .filter(SupplierModel.supplier.ilike(f"%{name}%"))
                .order_by(SupplierModel.id.desc())
                .all()
            )

            serialized_data = [{
                "id": supplier.id,
                "supplier": supplier.supplier,
                "added_date": supplier.added_date.strftime("%Y-%m-%d %H:%M:%S") if supplier.added_date else None,
                "updated_date": supplier.updated_date.strftime("%Y-%m-%d %H:%M:%S") if supplier.updated_date else None,
            } for supplier in data]

            return {"data": serialized_data}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def get_all(self, page=0, items_per_page=10):
        try:
            query = (
                self.db.query(
                    SupplierModel.id,
                    SupplierModel.supplier,
                    SupplierModel.added_date,
                    SupplierModel.updated_date,
                )
                .order_by(SupplierModel.id)
            )

            if page > 0:
                total_items = query.count()
                total_pages = (total_items + items_per_page - 1) // items_per_page

                if page < 1 or page > total_pages:
                    return {"status": "error", "message": "Invalid page number"}

                data = query.offset((page - 1) * items_per_page).limit(items_per_page).all()

                if not data:
                    return {"status": "error", "message": "No data found"}

                serialized_data = [{
                    "id": supplier.id,
                    "supplier": supplier.supplier,
                    "added_date": supplier.added_date.strftime("%Y-%m-%d %H:%M:%S") if supplier.added_date else None,
                    "updated_date": supplier.updated_date.strftime("%Y-%m-%d %H:%M:%S") if supplier.updated_date else None,
                } for supplier in data]

                return {
                    "total_items": total_items,
                    "total_pages": total_pages,
                    "current_page": page,
                    "items_per_page": items_per_page,
                    "data": serialized_data
                }

            else:
                data = query.all()

                serialized_data = [{
                    "id": supplier.id,
                    "supplier": supplier.supplier,
                    "added_date": supplier.added_date.strftime("%Y-%m-%d %H:%M:%S") if supplier.added_date else None,
                    "updated_date": supplier.updated_date.strftime("%Y-%m-%d %H:%M:%S") if supplier.updated_date else None,
                } for supplier in data]

                return serialized_data

        except Exception as e:
            error_message = str(e)
            return {"status": "error", "message": error_message}
    
    def get_list(self, page=0, items_per_page=10):
        try:
            data = (
                self.db.query(
                    SupplierModel.id,
                    SupplierModel.supplier,
                    SupplierModel.added_date
                )
                .order_by(SupplierModel.id)
            )

            if not data:
                return {"status": "error", "message": "No data found"}

            serialized_data = [{
                    "id": supplier.id,
                    "supplier": supplier.supplier,
                    "added_date": supplier.added_date.strftime("%Y-%m-%d %H:%M:%S") if supplier.added_date else None
                } for supplier in data]

            return {
                "data": serialized_data
            }
        except Exception as e:
            error_message = str(e)
            return {"status": "error", "message": error_message}
        
    def store(self, supplier_inputs):
        try:
            new_supplier = SupplierModel(
                supplier=supplier_inputs.supplier,
                added_date=datetime.now(),
                updated_date=datetime.now()
            )
    
            self.db.add(new_supplier)
            self.db.commit()
            self.db.refresh(new_supplier)

            return {
                "status": "Proveedor registrado exitosamente.",
                "supplier_id": new_supplier.id
            }

        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

    def update(self, id, supplier_inputs):
        existing_supplier = self.db.query(SupplierModel).filter(SupplierModel.id == id).one_or_none()

        if not existing_supplier:
            return "No data found"

        try:
            existing_supplier.supplier = supplier_inputs.supplier
            existing_supplier.updated_date = datetime.utcnow()

            self.db.commit()
            self.db.refresh(existing_supplier)
            return "Supplier updated successfully"
        except Exception as e:
            self.db.rollback()
            error_message = str(e)
            return {"status": "error", "message": error_message}
        
    def get(self, id):
        try:
            data_query = self.db.query(
                SupplierModel.id, 
                SupplierModel.supplier,
                SupplierModel.added_date,
                SupplierModel.updated_date,
            ).filter(SupplierModel.id == id).first()

            if data_query:
                supplier_data = {
                    "id": data_query.id,
                    "supplier": data_query.supplier,
                    "added_date": data_query.added_date.strftime("%Y-%m-%d %H:%M:%S") if data_query.added_date else None,
                    "updated_date": data_query.updated_date.strftime("%Y-%m-%d %H:%M:%S") if data_query.updated_date else None,
                }

                return {"supplier_data": supplier_data}

            else:
                return {"error": "No se encontraron datos para el campo especificado."}
            
        except Exception as e:
            return {"error": str(e)}
        
    def delete(self, id):
        try:
            data = self.db.query(SupplierModel).filter(SupplierModel.id == id).first()
            if data:
                self.db.delete(data)
                self.db.commit()
                return 'success'
            else:
                return "No data found"
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"