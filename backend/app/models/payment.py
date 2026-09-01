from typing import Any
from sqlalchemy import Column, Integer, String, Numeric, Text, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class Payment(Base):
    __tablename__ = "payments"
    __table_args__ = (
        CheckConstraint('amount > 0', name='check_payment_amount_positive'),
    )
    id: Any = Column(Integer, primary_key=True, index=True)
    business_id: Any = Column(Integer, ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    debt_id: Any = Column(Integer, ForeignKey("debts.id", ondelete="SET NULL"), nullable=True, index=True)
    sale_id: Any = Column(Integer, ForeignKey("sales.id", ondelete="SET NULL"), nullable=True, index=True)
    customer_id: Any = Column(Integer, ForeignKey("customers.id", ondelete="RESTRICT"), nullable=True, index=True)
    amount: Any = Column(Numeric(12, 2), server_default="0", nullable=False)
    payment_method: Any = Column(String(50), nullable=True)
    note: Any = Column(Text, nullable=True)
    payment_date: Any = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    created_by: Any = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at: Any = Column(DateTime(timezone=True), server_default=func.now())
    updated_at: Any = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    business: Any = relationship("Business", back_populates="payments")
    debt: Any = relationship("Debt", back_populates="payments")
    sale: Any = relationship("Sale", back_populates="payments")
    customer: Any = relationship("Customer", back_populates="payments")
    creator: Any = relationship("User", back_populates="payments_created")
