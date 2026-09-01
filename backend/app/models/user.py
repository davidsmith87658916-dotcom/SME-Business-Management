from typing import Any
import enum
from sqlalchemy import Column, Integer, String, DateTime, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class UserStatusEnum(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"

class User(Base):
    __tablename__ = "users"
    id: int = Column(Integer, primary_key=True, index=True) # type: ignore
    name: Any = Column(String(255), nullable=False)
    email: Any = Column(String(255), unique=True, index=True, nullable=False)
    phone: Any = Column(String(50), nullable=True)
    password: Any = Column(String(255), nullable=False)
    status: Any = Column(Enum(UserStatusEnum, name="user_status_enum"), server_default="ACTIVE", nullable=False)
    created_at: Any = Column(DateTime(timezone=True), server_default=func.now())
    updated_at: Any = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    memberships: Any = relationship("BusinessMember", back_populates="user", cascade="all, delete")
    sales_created: Any = relationship("Sale", back_populates="creator")
    purchases_created: Any = relationship("Purchase", back_populates="creator")
    payments_created: Any = relationship("Payment", back_populates="creator")
