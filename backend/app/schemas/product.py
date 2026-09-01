from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from decimal import Decimal
from datetime import datetime
from app.models.product import ProductStatusEnum
from app.models.stock_movement import MovementTypeEnum, ReferenceTypeEnum

# Category
class CategoryBase(BaseModel):
    name: str

class CategoryCreate(CategoryBase):
    business_id: int = 0

class CategoryUpdate(BaseModel):
    name: Optional[str] = None

class CategoryResponse(CategoryBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    business_id: int
    created_at: datetime
    updated_at: datetime

# Product
class ProductBase(BaseModel):
    name: str
    sku: Optional[str] = None
    barcode: Optional[str] = None
    cost_price: Decimal = Field(default=Decimal('0'), ge=Decimal('0'), max_digits=12, decimal_places=2)
    sell_price: Decimal = Field(default=Decimal('0'), ge=Decimal('0'), max_digits=12, decimal_places=2)
    stock_qty: Decimal = Field(default=Decimal('0'), ge=Decimal('0'), max_digits=12, decimal_places=2)
    unit: Optional[str] = None
    image: Optional[str] = None
    status: ProductStatusEnum = ProductStatusEnum.ACTIVE

class ProductCreate(ProductBase):
    business_id: int = 0
    category_id: Optional[int] = None

class ProductUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: Optional[str] = None
    sku: Optional[str] = None
    barcode: Optional[str] = None
    cost_price: Optional[Decimal] = Field(default=None, ge=Decimal('0'), max_digits=12, decimal_places=2)
    sell_price: Optional[Decimal] = Field(default=None, ge=Decimal('0'), max_digits=12, decimal_places=2)
    unit: Optional[str] = None
    image: Optional[str] = None
    status: Optional[ProductStatusEnum] = None
    category_id: Optional[int] = None

class ProductResponse(ProductBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    business_id: int
    category_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

# StockMovement
class StockMovementBase(BaseModel):
    type: MovementTypeEnum
    quantity: Decimal = Field(max_digits=12, decimal_places=2)
    reference_type: Optional[ReferenceTypeEnum] = None
    reference_id: Optional[int] = None
    note: Optional[str] = None

class StockMovementCreate(StockMovementBase):
    business_id: int = 0
    product_id: int

class StockMovementResponse(StockMovementBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    business_id: int
    product_id: int
    created_at: datetime

class StockAdjustmentCreate(BaseModel):
    product_id: int
    quantity: Decimal = Field(max_digits=12, decimal_places=2)
    note: str = Field(min_length=1, max_length=500)
