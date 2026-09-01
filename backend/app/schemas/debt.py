from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from decimal import Decimal
from datetime import datetime
from app.models.debt import DebtStatusEnum

class DebtBase(BaseModel):
    customer_id: int
    sale_id: Optional[int] = None
    total_amount: Decimal = Field(default=Decimal('0'), ge=Decimal('0'), max_digits=12, decimal_places=2)
    paid_amount: Decimal = Field(default=Decimal('0'), ge=Decimal('0'), max_digits=12, decimal_places=2)
    remaining_amount: Decimal = Field(default=Decimal('0'), ge=Decimal('0'), max_digits=12, decimal_places=2)
    due_date: Optional[datetime] = None
    status: DebtStatusEnum = DebtStatusEnum.OPEN

class DebtCreate(DebtBase):
    business_id: int = 0

class DebtUpdate(BaseModel):
    total_amount: Optional[Decimal] = Field(default=None, ge=Decimal('0'), max_digits=12, decimal_places=2)
    paid_amount: Optional[Decimal] = Field(default=None, ge=Decimal('0'), max_digits=12, decimal_places=2)
    remaining_amount: Optional[Decimal] = Field(default=None, ge=Decimal('0'), max_digits=12, decimal_places=2)
    due_date: Optional[datetime] = None
    status: Optional[DebtStatusEnum] = None

class DebtResponse(DebtBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    business_id: int
    created_at: datetime
    updated_at: datetime

