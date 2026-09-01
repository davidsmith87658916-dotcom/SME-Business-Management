from typing import Any
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class Supplier(Base):
    __tablename__ = "suppliers"
    id: Any = Column(Integer, primary_key=True, index=True)
    business_id: Any = Column(Integer, ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)
    name: Any = Column(String(255), nullable=False)
    phone: Any = Column(String(50), nullable=True)
    email: Any = Column(String(255), nullable=True)
    address: Any = Column(Text, nullable=True)
    created_at: Any = Column(DateTime(timezone=True), server_default=func.now())
    updated_at: Any = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    business: Any = relationship("Business", back_populates="suppliers")
    purchases: Any = relationship("Purchase", back_populates="supplier")
