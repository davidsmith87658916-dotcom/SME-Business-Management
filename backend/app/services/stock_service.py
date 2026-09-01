"""Compatibility imports for stock operations.

Stock writes are centralized in ``product_service`` so every quantity change and
its audit movement are committed in the same database transaction.
"""

from app.services.product_service import adjust_stock, get_stock_movements, record_stock_movement

__all__ = ["adjust_stock", "get_stock_movements", "record_stock_movement"]
