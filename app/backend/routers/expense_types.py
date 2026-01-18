from fastapi import APIRouter, Depends
from app.backend.db.database import get_db
from sqlalchemy.orm import Session
from app.backend.schemas import UserLogin, StoreExpenseType, ExpenseTypeList, UpdateExpenseType
from app.backend.classes.expense_type_class import ExpenseTypeClass
from app.backend.auth.auth_user import get_current_active_user

expense_types = APIRouter(
    prefix="/expense_types",
    tags=["Expense Types"]
)

@expense_types.post("/")
def index(expense_type_inputs: ExpenseTypeList, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = ExpenseTypeClass(db).get_all(expense_type_inputs.page)

    return {"message": data}

@expense_types.get("/list")
def list_all(session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = ExpenseTypeClass(db).get_list()

    return {"message": data}

@expense_types.post("/store")
def store(expense_type_inputs: StoreExpenseType, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = ExpenseTypeClass(db).store(expense_type_inputs)

    return {"message": data}

@expense_types.post("/update/{id}")
def update(id: int, expense_type_inputs: UpdateExpenseType, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = ExpenseTypeClass(db).update(id, expense_type_inputs)

    return {"message": data}

@expense_types.delete("/delete/{id}")
def delete(id: int, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = ExpenseTypeClass(db).delete(id)

    return {"message": data}

@expense_types.get("/edit/{id}")
def edit(id: int, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = ExpenseTypeClass(db).get(id)

    return {"message": data}
