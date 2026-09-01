from pydantic import BaseModel, ConfigDict, EmailStr, Field
from typing import Optional
from datetime import datetime
from typing import List
from app.schemas.sale import SaleResponse
from app.schemas.debt import DebtResponse
from app.schemas.payment import PaymentResponse

class CustomerBase(BaseModel):
    name: str
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    address: Optional[str] = None

class CustomerCreate(CustomerBase):
    business_id: int = 0

class CustomerUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    address: Optional[str] = None

class CustomerResponse(CustomerBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    business_id: int
    created_at: datetime
    updated_at: datetime

class CustomerHistoryResponse(BaseModel):
    sales: List[SaleResponse] = Field(default_factory=list)
    debts: List[DebtResponse] = Field(default_factory=list)
    payments: List[PaymentResponse] = Field(default_factory=list)
