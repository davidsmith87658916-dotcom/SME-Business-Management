from typing import Any
from sqlalchemy import Column, Integer, Numeric, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship
from app.database import Base

class SaleItem(Base):
    __tablename__ = "sale_items"
    __table_args__ = (
        CheckConstraint('quantity > 0', name='check_sitem_qty_positive'),
        CheckConstraint('price >= 0', name='check_sitem_price_positive'),
        CheckConstraint('cost_price >= 0', name='check_sitem_cost_positive'),
        CheckConstraint('discount >= 0', name='check_sitem_discount_positive'),
        CheckConstraint('subtotal >= 0', name='check_sitem_subtotal_positive'),
    )
    id: Any = Column(Integer, primary_key=True, index=True)
    sale_id: Any = Column(Integer, ForeignKey("sales.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id: Any = Column(Integer, ForeignKey("products.id", ondelete="SET NULL"), nullable=True, index=True)
    quantity: Any = Column(Numeric(12, 2), server_default="1", nullable=False)
    price: Any = Column(Numeric(12, 2), server_default="0", nullable=False)
    cost_price: Any = Column(Numeric(12, 2), server_default="0", nullable=False)
    discount: Any = Column(Numeric(12, 2), server_default="0", nullable=False)
    subtotal: Any = Column(Numeric(12, 2), server_default="0", nullable=False)

    sale: Any = relationship("Sale", back_populates="items")
    product: Any = relationship("Product", back_populates="sale_items")
