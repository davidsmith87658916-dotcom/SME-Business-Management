from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class PaymentCreate(BaseModel):
    amount: Decimal = Field(gt=Decimal("0"), max_digits=12, decimal_places=2)
    payment_method: str = Field(default="CASH", min_length=1, max_length=50)
    note: Optional[str] = Field(default=None, max_length=1000)
    payment_date: Optional[datetime] = None


class PaymentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    business_id: int
    debt_id: Optional[int] = None
    sale_id: Optional[int] = None
    customer_id: Optional[int] = None
    amount: Decimal
    payment_method: Optional[str] = None
    note: Optional[str] = None
    payment_date: Optional[datetime] = None
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime
