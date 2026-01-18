from fastapi import APIRouter, Depends
from app.backend.db.database import get_db
from sqlalchemy.orm import Session
from app.backend.schemas import UserLogin, StoreExpenseReport, ExpenseReportList, UpdateExpenseReport
from app.backend.classes.expense_report_class import ExpenseReportClass
from app.backend.auth.auth_user import get_current_active_user

expense_reports = APIRouter(
    prefix="/expense_reports",
    tags=["Expense Reports"]
)

@expense_reports.post("/")
def index(expense_report_inputs: ExpenseReportList, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = ExpenseReportClass(db).get_all(expense_report_inputs.page)

    return {"message": data}

@expense_reports.get("/list")
def list_all(session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = ExpenseReportClass(db).get_list()

    return {"message": data}

@expense_reports.post("/store")
def store(expense_report_inputs: StoreExpenseReport, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = ExpenseReportClass(db).store(expense_report_inputs)

    return {"message": data}

@expense_reports.post("/update/{id}")
def update(id: int, expense_report_inputs: UpdateExpenseReport, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = ExpenseReportClass(db).update(id, expense_report_inputs)

    return {"message": data}

@expense_reports.delete("/delete/{id}")
def delete(id: int, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = ExpenseReportClass(db).delete(id)

    return {"message": data}

@expense_reports.get("/edit/{id}")
def edit(id: int, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = ExpenseReportClass(db).get(id)

    return {"message": data}
