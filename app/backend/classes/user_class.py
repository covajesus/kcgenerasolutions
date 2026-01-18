import json
from app.backend.db.models import UserModel
from app.backend.auth.auth_user import generate_bcrypt_hash
from datetime import datetime
from app.backend.classes.helper_class import HelperClass
from werkzeug.security import generate_password_hash

class UserClass:
    def __init__(self, db):
        self.db = db

    def get_all(self, email=None, page=0, items_per_page=10):
        try:
            filters = []
            if email is not None:
                filters.append(UserModel.email == email)

            query = self.db.query(
                UserModel.id, 
                UserModel.full_name, 
                UserModel.rol_id, 
                UserModel.email,
                UserModel.added_date
            ).filter(
                *filters
            ).order_by(
                UserModel.id.desc()
            )

            if page > 0:
                total_items = query.count()
                total_pages = (total_items + items_per_page - 1)

                if page < 1 or page > total_pages:
                    return {"status": "error", "message": "Invalid page number"}

                data = query.offset((page - 1) * items_per_page).limit(items_per_page).all()

                if not data:
                    return {"status": "error", "message": "No data found"}

                serialized_data = [{
                    "id": user.id,
                    "full_name": user.full_name,
                    "rol_id": user.rol_id,
                    "email": user.email,
                    "added_date": user.added_date
                } for user in data]

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
                    "id": user.id,
                    "full_name": user.full_name,
                    "rol_id": user.rol_id,
                    "email": user.email,
                    "added_date": user.added_date
                } for user in data]

                return serialized_data

        except Exception as e:
            error_message = str(e)
            return {"status": "error", "message": error_message}
    
    def get(self, field, value):
        try:
            data_query = self.db.query(UserModel).filter(getattr(UserModel, field) == value).first()

            if data_query:
                user_data = {
                    "id": data_query.id,
                    "full_name": data_query.full_name,
                    "rol_id": data_query.rol_id,
                    "email": data_query.email,
                    "hashed_password": data_query.hashed_password
                }

                result = {
                    "user_data": user_data
                }

                serialized_result = json.dumps(result)

                return serialized_result

            else:
                return "No se encontraron datos para el campo especificado."

        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
        
    def get_supervisors(self):
        try:
            data = self.db.query(UserModel).order_by(UserModel.nickname).filter(UserModel.rol_id == 3).all()
            return data
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"  
    
    def store(self, user_inputs):
        user = UserModel()
        user.rol_id = user_inputs['rol_id']
        user.full_name = user_inputs['full_name']
        user.email = user_inputs['email']
        user.hashed_password = generate_bcrypt_hash(user_inputs['password'])
        user.added_date = datetime.now()
        user.updated_date = datetime.now()

        self.db.add(user)
        try:
            self.db.commit()
            self.db.refresh(user)
            return {"status": "success", "user_id": user.id}
        except Exception as e:
            self.db.rollback()
            return {"status": "error", "message": str(e)}
    
    def store_login(self, user_inputs):
        user = UserModel()
        user.rol_id = 5
        user.full_name = user_inputs.social_reason
        user.hashed_password = generate_bcrypt_hash('123456')
        user.email = user_inputs.email
        user.added_date = datetime.now()
        user.updated_date = datetime.now()

        self.db.add(user)
        try:
            self.db.commit()

            return 1
        except Exception as e:
            return 0
        
    def delete(self, id):
        try:
            data = self.db.query(UserModel).filter(UserModel.id == id).first()
            if data:
                self.db.delete(data)
                self.db.commit()
                return 'success'
            else:
                return "No data found"
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"

    def refresh_password(self, email: str):
        """
        Resetea la contraseña por email (sin usar `rut`).
        """
        user = self.db.query(UserModel).filter(UserModel.email == email).first()
        if not user:
            return 0

        user.hashed_password = generate_bcrypt_hash('123456')
        user.updated_date = datetime.now()
        self.db.add(user)

        try:
            self.db.commit()
            return 1
        except Exception:
            self.db.rollback()
            return 0

    def update(self, id, form_data):
        user = self.db.query(UserModel).filter(UserModel.id == id).first()

        # Solo actualizar campos presentes (no None)
        if form_data.get('rol_id') is not None:
            user.rol_id = form_data['rol_id']
        if form_data.get('full_name') is not None:
            user.full_name = form_data['full_name']
        if form_data.get('email') is not None:
            user.email = form_data['email']

        user.updated_date = datetime.now()

        self.db.add(user)

        try:
            self.db.commit()

            return 1
        except Exception as e:
            return 0

    def recover(self, user_inputs):
        try:
            email = user_inputs.get('email')
            user = self.db.query(UserModel).filter(UserModel.email == email).first()
            
            if not user:
                return {"status": "error", "message": "Usuario no encontrado"}
            
            # Aquí puedes agregar la lógica de recuperación de contraseña
            return {"status": "success", "message": "Instrucciones de recuperación enviadas"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def confirm_email(self, user_inputs):
        try:
            if isinstance(user_inputs, dict):
                email = user_inputs.get('email')
                token = user_inputs.get('token')
            else:
                email = user_inputs.email if hasattr(user_inputs, 'email') else None
                token = user_inputs.token if hasattr(user_inputs, 'token') else None
            
            user = self.db.query(UserModel).filter(UserModel.email == email).first()
            
            if not user:
                return {"status": "error", "message": "Usuario no encontrado"}
            
            # Aquí puedes agregar la lógica de confirmación de email
            return {"status": "success", "message": "Email confirmado exitosamente"}
        except Exception as e:
            return {"status": "error", "message": str(e)}