from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.purchase import PurchaseStatusEnum


class PurchaseItemCreate(BaseModel):
    product_id: int
    quantity: Decimal = Field(default=Decimal("1"), gt=Decimal("0"), max_digits=12, decimal_places=2)
    cost_price: Decimal = Field(ge=Decimal("0"), max_digits=12, decimal_places=2)


class PurchaseItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    purchase_id: int
    product_id: Optional[int] = None
    quantity: Decimal
    cost_price: Decimal
    subtotal: Decimal


class PurchaseCreate(BaseModel):
    business_id: int = 0
    supplier_id: int
    invoice_no: Optional[str] = Field(default=None, max_length=100)
    paid_amount: Decimal = Field(default=Decimal("0"), ge=Decimal("0"), max_digits=12, decimal_places=2)
    purchase_date: Optional[datetime] = None
    items: List[PurchaseItemCreate] = Field(default_factory=list, min_length=1)


class PurchaseUpdate(BaseModel):
    supplier_id: Optional[int] = None
    invoice_no: Optional[str] = Field(default=None, max_length=100)
    paid_amount: Optional[Decimal] = Field(default=None, ge=Decimal("0"), max_digits=12, decimal_places=2)
    status: Optional[PurchaseStatusEnum] = None
    purchase_date: Optional[datetime] = None


class PurchaseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    business_id: int
    supplier_id: Optional[int] = None
    invoice_no: Optional[str] = None
    total_amount: Decimal
    paid_amount: Decimal
    status: PurchaseStatusEnum
    purchase_date: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    items: List[PurchaseItemResponse] = Field(default_factory=list)
