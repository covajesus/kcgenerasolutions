from fastapi import APIRouter, Depends
from app.backend.db.database import get_db
from sqlalchemy.orm import Session
from app.backend.schemas import UserLogin, SupplierSearch
from app.backend.classes.supplier_class import SupplierClass
from app.backend.auth.auth_user import get_current_active_user

suppliers = APIRouter(
    prefix="/suppliers",
    tags=["Suppliers"]
)

@suppliers.post("/search")
def search(
    supplier_inputs: SupplierSearch,
    session_user: UserLogin = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    data = SupplierClass(db).search(supplier_inputs.supplier_name)
    return {"message": data}