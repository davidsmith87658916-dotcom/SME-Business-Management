from typing import Any
import enum
from sqlalchemy import Column, Integer, Enum, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class RoleEnum(str, enum.Enum):
    owner = "owner"
    staff = "staff"

class BusinessMember(Base):
    __tablename__ = "business_members"
    __table_args__ = (
        UniqueConstraint("user_id", "business_id", name="uq_user_business"),
    )
    
    id: Any = Column(Integer, primary_key=True, index=True)
    user_id: Any = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    business_id: Any = Column(Integer, ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)
    role: Any = Column(Enum(RoleEnum, name="role_enum"), server_default="staff", nullable=False)
    created_at: Any = Column(DateTime(timezone=True), server_default=func.now())
    updated_at: Any = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user: Any = relationship("User", back_populates="memberships")
    business: Any = relationship("Business", back_populates="members")
