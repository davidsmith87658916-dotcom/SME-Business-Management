from typing import Any
import enum
from sqlalchemy import Column, Integer, Numeric, Text, Enum, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class MovementTypeEnum(str, enum.Enum):
    IN = "IN"
    OUT = "OUT"
    ADJUST = "ADJUST"
    RETURN = "RETURN"

class ReferenceTypeEnum(str, enum.Enum):
    SALE = "SALE"
    PURCHASE = "PURCHASE"
    ADJUST = "ADJUST"
    RETURN = "RETURN"

class StockMovement(Base):
    __tablename__ = "stock_movements"
    __table_args__ = (
        CheckConstraint('quantity <> 0', name='check_stock_movement_nonzero'),
    )
    id: Any = Column(Integer, primary_key=True, index=True)
    business_id: Any = Column(Integer, ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id: Any = Column(Integer, ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True)
    type: Any = Column(Enum(MovementTypeEnum, name="movement_type_enum"), nullable=False)
    quantity: Any = Column(Numeric(12, 2), server_default="0", nullable=False)
    reference_type: Any = Column(Enum(ReferenceTypeEnum, name="reference_type_enum"), nullable=True, index=True)
    reference_id: Any = Column(Integer, nullable=True)
    note: Any = Column(Text, nullable=True)
    created_at: Any = Column(DateTime(timezone=True), server_default=func.now())

    business: Any = relationship("Business", back_populates="stock_movements")
    product: Any = relationship("Product", back_populates="stock_movements")
