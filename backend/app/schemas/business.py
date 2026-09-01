from pydantic import BaseModel, ConfigDict, field_validator
from typing import Optional
from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from app.models.business_member import RoleEnum

class BusinessBase(BaseModel):
    name: str
    phone: Optional[str] = None
    address: Optional[str] = None
    logo: Optional[str] = None
    currency: str = "USD"
    timezone: str = "UTC"

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, value: str) -> str:
        try:
            ZoneInfo(value)
        except ZoneInfoNotFoundError as exc:
            raise ValueError("Invalid IANA timezone") from exc
        return value

class BusinessCreate(BusinessBase):
    pass

class BusinessUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    logo: Optional[str] = None
    currency: Optional[str] = None
    timezone: Optional[str] = None

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        try:
            ZoneInfo(value)
        except ZoneInfoNotFoundError as exc:
            raise ValueError("Invalid IANA timezone") from exc
        return value

class BusinessResponse(BusinessBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime

class BusinessMemberBase(BaseModel):
    role: RoleEnum = RoleEnum.staff

class BusinessMemberCreate(BusinessMemberBase):
    user_id: int
    business_id: int = 0

class BusinessMemberUpdate(BaseModel):
    role: Optional[RoleEnum] = None

class BusinessMemberResponse(BusinessMemberBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    business_id: int
    created_at: datetime
    updated_at: datetime
