from typing import Any
from sqlalchemy import Column, Integer, Numeric, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship
from app.database import Base

class PurchaseItem(Base):
    __tablename__ = "purchase_items"
    __table_args__ = (
        CheckConstraint('quantity > 0', name='check_pitem_qty_positive'),
        CheckConstraint('cost_price >= 0', name='check_pitem_cost_positive'),
        CheckConstraint('subtotal >= 0', name='check_pitem_subtotal_positive'),
    )
    
    id: Any = Column(Integer, primary_key=True, index=True)
    purchase_id: Any = Column(Integer, ForeignKey("purchases.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id: Any = Column(Integer, ForeignKey("products.id", ondelete="SET NULL"), nullable=True, index=True)
    quantity: Any = Column(Numeric(12, 2), server_default="1", nullable=False)
    cost_price: Any = Column(Numeric(12, 2), server_default="0", nullable=False)
    subtotal: Any = Column(Numeric(12, 2), server_default="0", nullable=False)

    purchase: Any = relationship("Purchase", back_populates="items")
    product: Any = relationship("Product", back_populates="purchase_items")
