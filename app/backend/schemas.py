from pydantic import BaseModel, Field, EmailStr, validator
from fastapi import UploadFile, File
from typing import Union, List, Dict, Optional
from datetime import datetime, date
from decimal import Decimal
from fastapi import Form
from typing import List
from typing import Optional
import json

class UserLogin(BaseModel):
    rol_id: Union[int, None]
    full_name: Union[str, None]
    email: Union[str, None]
    hashed_password: Union[str, None]

class Rol(BaseModel):
    rol: str

class UpdateRol(BaseModel):
    rol: Optional[str] = None

class StoreUser(BaseModel):
    full_name: str
    password: str
    email: str
    rol_id: int

class User(BaseModel):
    rol_id: int
    full_name: str
    email: str
    password: str

class UpdateUser(BaseModel):
    rol_id: int = None
    full_name: str = None
    email: str = None

class UserList(BaseModel):
    email: Optional[str] = None
    page: int

class RecoverUser(BaseModel):
    email: str

class ConfirmEmail(BaseModel):
    email: str
    token: Optional[str] = None

class UpdateCustomer(BaseModel):
    social_reason: str
    identification_number: str
    activity: str
    address: str
    phone: str
    email: str
    region_id: int
    commune_id: int
    product_discounts: Optional[Dict[int, float]] = {}

class UpdateCustomerProfile(BaseModel):
    social_reason: Optional[str] = None
    activity: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    region_id: Optional[int] = None
    commune_id: Optional[int] = None

class StoreCustomer(BaseModel):
    social_reason: str
    identification_number: str
    activity: str
    address: str
    phone: str
    email: str
    region_id: int
    commune_id: int
    product_discounts: Optional[Dict[int, float]] = {}

class CustomerList(BaseModel):
    page: int
    name: Optional[str] = None
    rut: Optional[str] = None

class CategoryList(BaseModel):
    page: int

class InventoryList(BaseModel):
    page: int

class ProductList(BaseModel):
    page: int
    supplier_id: Optional[int] = None
    product_id: Optional[int] = None

class StoreSupplier(BaseModel):
    supplier: str

class StoreCategory(BaseModel):
    category: str
    public_name: str
    color: str

class UpdateCategory(BaseModel):
    category: str
    public_name: str
    color: str

class ExpenseTypeList(BaseModel):
    page: int

class StoreExpenseType(BaseModel):
    expense_type: str

class UpdateExpenseType(BaseModel):
    expense_type: str

class ExpenseReportList(BaseModel):
    page: int

class ExpenseReportSearch(BaseModel):
    page: int = 0
    company: Optional[str] = None
    company_name: Optional[str] = None
    document_number: Optional[str] = None

class ReportGenerate(BaseModel):
    since_date: str
    # el front envía until_date
    until_date: str
    # compatibilidad si algún cliente aún manda end_date
    end_date: Optional[str] = None

class StoreExpenseReport(BaseModel):
    expense_type_id: int
    document_number: int
    company: str
    amount: str
    document_date: Optional[datetime] = None
    file: Optional[str] = None

    @classmethod
    def as_form(
        cls,
        expense_type_id: int = Form(...),
        document_number: int = Form(...),
        company: str = Form(...),
        amount: str = Form(...),
        document_date: Optional[datetime] = Form(None),
    ):
        return cls(
            expense_type_id=expense_type_id,
            document_number=document_number,
            company=company,
            amount=amount,
            document_date=document_date,
            file=None,
        )

class UpdateExpenseReport(BaseModel):
    expense_type_id: int
    document_number: int
    company: str
    amount: str
    document_date: Optional[datetime] = None
    file: Optional[str] = None

    @classmethod
    def as_form(
        cls,
        expense_type_id: int = Form(...),
        document_number: int = Form(...),
        company: str = Form(...),
        amount: str = Form(...),
        document_date: Optional[datetime] = Form(None),
    ):
        return cls(
            expense_type_id=expense_type_id,
            document_number=document_number,
            company=company,
            amount=amount,
            document_date=document_date,
            file=None,
        )

class UpdateSupplier(BaseModel):
    supplier: str

class SupplierSearch(BaseModel):
    supplier_name: str

class AddAdjustmentInput(BaseModel):
    user_id: int
    inventory_id: int
    product_id: Optional[int] = None  # Opcional, se puede obtener del inventario
    location_id: int
    stock: int
    public_sale_price: int
    private_sale_price: int
    unit_cost: int
    lot_number: str  # Número de lote requerido

class RemoveAdjustmentInput(BaseModel):
    user_id: int
    inventory_id: int
    product_id: Optional[int] = None  # Opcional, se puede obtener del inventario
    stock: int  # Solo cantidad

class StoreProduct(BaseModel):
    supplier_id: int
    category_id: int
    unit_measure_id: int
    code: str
    product: str
    original_unit_cost: str
    discount_percentage: str
    final_unit_cost: str
    short_description: str
    description: str
    quantity_per_package: Union[str, None]
    quantity_per_pallet: Union[str, None]
    weight_per_pallet: Union[str, None]
    weight_per_unit: Union[str, None]
    is_compound: int
    compound_product_id: Union[int, None]

    @classmethod
    def as_form(cls,
                    supplier_id: int = Form(...),
                    category_id: int = Form(...),
                    unit_measure_id: int = Form(...),
                    code: str = Form(...),
                    product: str = Form(...),
                    original_unit_cost: str = Form(...),
                    discount_percentage: str = Form(...),
                    final_unit_cost: str = Form(...),
                    description: str = Form(...),
                    quantity_per_package: Optional[str] = Form(None),
                    quantity_per_pallet: Optional[str] = Form(None),
                    weight_per_pallet: Optional[str] = Form(None),
                    weight_per_unit: Optional[str] = Form(None),
                    short_description: str = Form(...),
                    is_compound: int = Form(...),
                    compound_product_id: Union[int, None] = Form(None)
                ):
        return cls(
            supplier_id=supplier_id,
            category_id=category_id,
            unit_measure_id=unit_measure_id,
            code=code,
            product=product,
            original_unit_cost=original_unit_cost,
            discount_percentage=discount_percentage,
            final_unit_cost=final_unit_cost,
            description=description,
            quantity_per_package=quantity_per_package,
            quantity_per_pallet=quantity_per_pallet,
            weight_per_pallet=weight_per_pallet,
            weight_per_unit=weight_per_unit,
            short_description=short_description,
            is_compound=is_compound,
            compound_product_id=compound_product_id
        )
    
class SupplierList(BaseModel):
    page: int

class StoreInventory(BaseModel):
    user_id: int
    product_id: int
    location_id: int
    stock: int
    unit_cost: int
    public_sale_price: int
    private_sale_price: int
    minimum_stock: int
    maximum_stock: int
    lot_number: str
    arrival_date: date
    shopping_id: Optional[int] = None  # Para cálculo automático de unit_cost

class UpdateSettings(BaseModel):
    tax_value: int
    identification_number: str
    account_type: str
    account_number: str
    account_name: str
    account_email: str
    bank: str
    delivery_cost: int
    shop_address: str
    payment_card_url: str
    prepaid_discount: Optional[int] = 0
    phone: str

class SupplierCategoryCreate(BaseModel):
    supplier_id: int
    category_id: int

class SupplierCategoryUpdate(BaseModel):
    supplier_id: Optional[int] = None
    category_id: Optional[int] = None

class SupplierCategoryList(BaseModel):
    page: int = 1

class SupplierCategoryResponse(BaseModel):
    id: int
    supplier_id: int
    category_id: int
    added_date: Optional[datetime] = None
    updated_date: Optional[datetime] = None
    
    class Config:
        from_attributes = True