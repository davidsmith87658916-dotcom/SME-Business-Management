from typing import Any
import enum
from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey, UniqueConstraint, Enum, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class ProductStatusEnum(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"

class Product(Base):
    __tablename__ = "products"
    __table_args__ = (
        UniqueConstraint("business_id", "sku", name="uq_business_product_sku"),
        UniqueConstraint("business_id", "barcode", name="uq_business_product_barcode"),
        CheckConstraint('cost_price >= 0', name='check_cost_price_positive'),
        CheckConstraint('sell_price >= 0', name='check_sell_price_positive'),
        CheckConstraint('stock_qty >= 0', name='check_stock_qty_positive'),
    )

    id: Any = Column(Integer, primary_key=True, index=True)
    business_id: Any = Column(Integer, ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)
    category_id: Any = Column(Integer, ForeignKey("categories.id", ondelete="SET NULL"), nullable=True)
    name: Any = Column(String(255), nullable=False)
    sku: Any = Column(String(100), index=True, nullable=True)
    barcode: Any = Column(String(100), index=True, nullable=True)
    cost_price: Any = Column(Numeric(12, 2), server_default="0", nullable=False)
    sell_price: Any = Column(Numeric(12, 2), server_default="0", nullable=False)
    stock_qty: Any = Column(Numeric(12, 2), server_default="0", nullable=False)
    unit: Any = Column(String(50), nullable=True)
    image: Any = Column(String(255), nullable=True)
    status: Any = Column(Enum(ProductStatusEnum, name="product_status_enum"), server_default="ACTIVE", nullable=False)
    created_at: Any = Column(DateTime(timezone=True), server_default=func.now())
    updated_at: Any = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    business: Any = relationship("Business", back_populates="products")
    category: Any = relationship("Category", back_populates="products")
    sale_items: Any = relationship("SaleItem", back_populates="product")
    stock_movements: Any = relationship("StockMovement", back_populates="product")
    purchase_items: Any = relationship("PurchaseItem", back_populates="product")
