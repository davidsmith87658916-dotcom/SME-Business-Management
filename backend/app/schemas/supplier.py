from pydantic import BaseModel, ConfigDict, EmailStr
from typing import Optional
from datetime import datetime

class SupplierBase(BaseModel):
    name: str
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    address: Optional[str] = None

class SupplierCreate(SupplierBase):
    business_id: int = 0

class SupplierUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    address: Optional[str] = None

class SupplierResponse(SupplierBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    business_id: int
    created_at: datetime
    updated_at: datetime
