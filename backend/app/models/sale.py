from typing import Any
import enum
from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey, UniqueConstraint, Enum, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class SaleStatusEnum(str, enum.Enum):
    DRAFT = "DRAFT"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"

class PaymentStatusEnum(str, enum.Enum):
    UNPAID = "UNPAID"
    PARTIAL = "PARTIAL"
    PAID = "PAID"

class Sale(Base):
    __tablename__ = "sales"
    __table_args__ = (
        UniqueConstraint("business_id", "invoice_no", name="uq_business_sale_invoice"),
        CheckConstraint('total_amount >= 0', name='check_sale_total_amount_positive'),
        CheckConstraint('discount_amount >= 0', name='check_sale_discount_amount_positive'),
        CheckConstraint('paid_amount >= 0', name='check_sale_paid_amount_positive'),
        CheckConstraint('paid_amount <= total_amount', name='check_sale_paid_not_over_total'),
    )

    id: Any = Column(Integer, primary_key=True, index=True)
    business_id: Any = Column(Integer, ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    customer_id: Any = Column(Integer, ForeignKey("customers.id", ondelete="SET NULL"), nullable=True, index=True)
    invoice_no: Any = Column(String(100), index=True, nullable=False)
    total_amount: Any = Column(Numeric(12, 2), server_default="0", nullable=False)
    discount_amount: Any = Column(Numeric(12, 2), server_default="0", nullable=False)
    paid_amount: Any = Column(Numeric(12, 2), server_default="0", nullable=False)
    
    status: Any = Column(Enum(SaleStatusEnum, name="sale_status_enum"), server_default="DRAFT", nullable=False)
    payment_status: Any = Column(Enum(PaymentStatusEnum, name="payment_status_enum"), server_default="UNPAID", nullable=False)
    payment_method: Any = Column(String(50), nullable=True)
    
    sale_date: Any = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    completed_at: Any = Column(DateTime(timezone=True), nullable=True)
    created_by: Any = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at: Any = Column(DateTime(timezone=True), server_default=func.now())
    updated_at: Any = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    business: Any = relationship("Business", back_populates="sales")
    customer: Any = relationship("Customer", back_populates="sales")
    creator: Any = relationship("User", back_populates="sales_created")
    items: Any = relationship("SaleItem", back_populates="sale", cascade="all, delete")
    debts: Any = relationship("Debt", back_populates="sale")
    payments: Any = relationship("Payment", back_populates="sale")
