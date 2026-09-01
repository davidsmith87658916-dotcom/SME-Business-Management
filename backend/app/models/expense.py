from typing import Any
from sqlalchemy import Column, Integer, String, Numeric, Text, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class Expense(Base):
    __tablename__ = "expenses"
    __table_args__ = (
        CheckConstraint('amount > 0', name='check_expense_amount_positive'),
    )
    
    id: Any = Column(Integer, primary_key=True, index=True)
    business_id: Any = Column(Integer, ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    category_id: Any = Column(Integer, ForeignKey("expense_categories.id", ondelete="SET NULL"), nullable=True)
    title: Any = Column(String(255), nullable=False)
    amount: Any = Column(Numeric(12, 2), server_default="0", nullable=False)
    expense_date: Any = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    note: Any = Column(Text, nullable=True)
    created_at: Any = Column(DateTime(timezone=True), server_default=func.now())
    updated_at: Any = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    business: Any = relationship("Business", back_populates="expenses")
    category: Any = relationship("ExpenseCategory", back_populates="expenses")
