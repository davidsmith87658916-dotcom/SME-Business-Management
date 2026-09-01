from typing import Any
import enum
from sqlalchemy import Column, Integer, Numeric, Enum, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class DebtStatusEnum(str, enum.Enum):
    OPEN = "OPEN"
    PARTIAL = "PARTIAL"
    PAID = "PAID"

class Debt(Base):
    __tablename__ = "debts"
    __table_args__ = (
        CheckConstraint('total_amount >= 0', name='check_debt_total_positive'),
        CheckConstraint('paid_amount >= 0', name='check_debt_paid_positive'),
        CheckConstraint('remaining_amount >= 0', name='check_debt_remaining_positive'),
        CheckConstraint('paid_amount <= total_amount', name='check_debt_paid_not_over_total'),
        CheckConstraint('remaining_amount = total_amount - paid_amount', name='check_debt_balance_consistent'),
    )
    
    id: Any = Column(Integer, primary_key=True, index=True)
    business_id: Any = Column(Integer, ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    customer_id: Any = Column(Integer, ForeignKey("customers.id", ondelete="RESTRICT"), nullable=False, index=True)
    sale_id: Any = Column(Integer, ForeignKey("sales.id", ondelete="SET NULL"), nullable=True, unique=True, index=True)
    total_amount: Any = Column(Numeric(12, 2), server_default="0", nullable=False)
    paid_amount: Any = Column(Numeric(12, 2), server_default="0", nullable=False)
    remaining_amount: Any = Column(Numeric(12, 2), server_default="0", nullable=False)
    due_date: Any = Column(DateTime(timezone=True), nullable=True)
    status: Any = Column(Enum(DebtStatusEnum, name="debt_status_enum"), server_default="OPEN", nullable=False)
    created_at: Any = Column(DateTime(timezone=True), server_default=func.now())
    updated_at: Any = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    business: Any = relationship("Business", back_populates="debts")
    customer: Any = relationship("Customer", back_populates="debts")
    sale: Any = relationship("Sale", back_populates="debts")
    payments: Any = relationship("Payment", back_populates="debt")
