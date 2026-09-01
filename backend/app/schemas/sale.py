from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.sale import PaymentStatusEnum, SaleStatusEnum


class SaleItemCreate(BaseModel):
    product_id: int
    quantity: Decimal = Field(default=Decimal("1"), gt=Decimal("0"), max_digits=12, decimal_places=2)
    price: Optional[Decimal] = Field(default=None, ge=Decimal("0"), max_digits=12, decimal_places=2)
    discount: Decimal = Field(default=Decimal("0"), ge=Decimal("0"), max_digits=12, decimal_places=2)


class SaleItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sale_id: int
    product_id: Optional[int] = None
    quantity: Decimal
    price: Decimal
    cost_price: Decimal
    discount: Decimal
    subtotal: Decimal


class SaleCreate(BaseModel):
    business_id: int = 0
    customer_id: Optional[int] = None
    invoice_no: Optional[str] = Field(default=None, max_length=100)
    discount_amount: Decimal = Field(default=Decimal("0"), ge=Decimal("0"), max_digits=12, decimal_places=2)
    paid_amount: Decimal = Field(default=Decimal("0"), ge=Decimal("0"), max_digits=12, decimal_places=2)
    payment_method: Optional[str] = Field(default=None, max_length=50)
    sale_date: Optional[datetime] = None
    save_as_draft: bool = False
    items: List[SaleItemCreate] = Field(default_factory=list, min_length=1)


class SaleComplete(BaseModel):
    paid_amount: Decimal = Field(default=Decimal("0"), ge=Decimal("0"), max_digits=12, decimal_places=2)
    payment_method: Optional[str] = Field(default=None, max_length=50)
    sale_date: Optional[datetime] = None


class SaleUpdate(BaseModel):
    customer_id: Optional[int] = None
    invoice_no: Optional[str] = Field(default=None, max_length=100)
    discount_amount: Optional[Decimal] = Field(default=None, ge=Decimal("0"), max_digits=12, decimal_places=2)
    paid_amount: Optional[Decimal] = Field(default=None, ge=Decimal("0"), max_digits=12, decimal_places=2)
    payment_method: Optional[str] = Field(default=None, max_length=50)
    sale_date: Optional[datetime] = None


class SaleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    business_id: int
    customer_id: Optional[int] = None
    invoice_no: Optional[str] = None
    total_amount: Decimal
    discount_amount: Decimal
    paid_amount: Decimal
    status: SaleStatusEnum
    payment_status: PaymentStatusEnum
    payment_method: Optional[str] = None
    sale_date: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    items: List[SaleItemResponse] = Field(default_factory=list)
