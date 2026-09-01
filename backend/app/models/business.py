from typing import Any
from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class Business(Base):
    __tablename__ = "businesses"
    id: Any = Column(Integer, primary_key=True, index=True)
    name: Any = Column(String(255), nullable=False)
    phone: Any = Column(String(50), nullable=True)
    address: Any = Column(Text, nullable=True)
    logo: Any = Column(String(255), nullable=True)
    currency: Any = Column(String(10), server_default="USD")
    timezone: Any = Column(String(50), server_default="UTC")
    created_at: Any = Column(DateTime(timezone=True), server_default=func.now())
    updated_at: Any = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    members: Any = relationship("BusinessMember", back_populates="business", cascade="all, delete")
    customers: Any = relationship("Customer", back_populates="business", cascade="all, delete")
    suppliers: Any = relationship("Supplier", back_populates="business", cascade="all, delete")
    categories: Any = relationship("Category", back_populates="business", cascade="all, delete")
    products: Any = relationship("Product", back_populates="business", cascade="all, delete")
    sales: Any = relationship("Sale", back_populates="business", cascade="all, delete")
    purchases: Any = relationship("Purchase", back_populates="business", cascade="all, delete")
    expense_categories: Any = relationship("ExpenseCategory", back_populates="business", cascade="all, delete")
    expenses: Any = relationship("Expense", back_populates="business", cascade="all, delete")
    debts: Any = relationship("Debt", back_populates="business", cascade="all, delete")
    payments: Any = relationship("Payment", back_populates="business", cascade="all, delete")
    stock_movements: Any = relationship("StockMovement", back_populates="business", cascade="all, delete")
