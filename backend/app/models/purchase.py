from typing import Any
import enum
from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey, UniqueConstraint, Enum, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class PurchaseStatusEnum(str, enum.Enum):
    DRAFT = "DRAFT"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"

class Purchase(Base):
    __tablename__ = "purchases"
    __table_args__ = (
        UniqueConstraint("business_id", "invoice_no", name="uq_business_purchase_invoice"),
        CheckConstraint('total_amount >= 0', name='check_purc_total_positive'),
        CheckConstraint('paid_amount >= 0', name='check_purc_paid_positive'),
        CheckConstraint('paid_amount <= total_amount', name='check_purc_paid_not_over_total'),
    )

    id: Any = Column(Integer, primary_key=True, index=True)
    business_id: Any = Column(Integer, ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    supplier_id: Any = Column(Integer, ForeignKey("suppliers.id", ondelete="SET NULL"), nullable=True, index=True)
    invoice_no: Any = Column(String(100), nullable=True, index=True)
    total_amount: Any = Column(Numeric(12, 2), server_default="0", nullable=False)
    paid_amount: Any = Column(Numeric(12, 2), server_default="0", nullable=False)
    
    status: Any = Column(Enum(PurchaseStatusEnum, name="purchase_status_enum"), server_default="DRAFT", nullable=False)
    
    purchase_date: Any = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    completed_at: Any = Column(DateTime(timezone=True), nullable=True)
    created_by: Any = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at: Any = Column(DateTime(timezone=True), server_default=func.now())
    updated_at: Any = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    business: Any = relationship("Business", back_populates="purchases")
    supplier: Any = relationship("Supplier", back_populates="purchases")
    creator: Any = relationship("User", back_populates="purchases_created")
    items: Any = relationship("PurchaseItem", back_populates="purchase", cascade="all, delete")
