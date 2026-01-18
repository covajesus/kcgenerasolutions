from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import uvicorn
import os
from fastapi.middleware.cors import CORSMiddleware
from app.backend.routers.authentications import authentications
from app.backend.routers.users import users
from app.backend.routers.files import files
from app.backend.routers.suppliers import suppliers
from app.backend.routers.categories import categories
from app.backend.routers.settings import settings
from app.backend.routers.customers import customers
from app.backend.routers.supplier_categories import supplier_categories
from app.backend.routers.whatsapp import whatsapp
from app.backend.routers.expense_types import expense_types
from app.backend.routers.expense_reports import expense_reports
from app.backend.routers.reports import reports
from app.backend.routers.rols import rols

app = FastAPI(root_path="/api")
application = app

#FILES_DIR = "C:/Users/jesus/OneDrive/Escritorio/backend-lacasadelvitrificado/files"

# Montar como directorio estático
#app.mount("/files", StaticFiles(directory=FILES_DIR), name="files")

os.environ['SECRET_KEY'] = '7de4c36b48fce8dcb3a4bb527ba62d789ebf3d3a7582472ee49d430b01a7f868'
os.environ['ALGORITHM'] = 'HS256'

origins = [
    "*",
    "https://newerp-ghdegyc9cpcpc6gq.eastus-01.azurewebsites.net",
    
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(authentications)
app.include_router(users)
app.include_router(files)
app.include_router(suppliers)
app.include_router(categories)
app.include_router(settings)
app.include_router(customers)
app.include_router(supplier_categories)
app.include_router(whatsapp)
app.include_router(expense_types)
app.include_router(expense_reports)
app.include_router(reports)
app.include_router(rols)

if __name__ == "__main__":
    uvicorn.run("main:app", port=8000, reload=True)
