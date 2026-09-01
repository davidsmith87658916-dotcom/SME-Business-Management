from pydantic import BaseModel
from typing import List, Optional
from decimal import Decimal

# Sales Report
class TopProduct(BaseModel):
    product_id: Optional[int] = None
    product_name: str
    total_quantity_sold: Decimal
    total_revenue: Decimal

class SalesReportResponse(BaseModel):
    total_sales_amount: Decimal
    total_transactions: int
    top_selling_products: List[TopProduct]

# Profit Report (can just reuse Dashboard logic, but we make a dedicated schema for consistency)
class ProfitReportResponse(BaseModel):
    total_sales: Decimal
    total_cogs: Decimal
    total_expenses: Decimal
    net_profit: Decimal

# Inventory Report
class LowStockProduct(BaseModel):
    product_id: int
    product_name: str
    current_stock: Decimal
    cost_price: Decimal

class InventoryReportResponse(BaseModel):
    total_stock_value: Decimal
    total_products_count: int
    low_stock_items: List[LowStockProduct]

# Customer Report
class CustomerDebt(BaseModel):
    customer_id: int
    customer_name: str
    total_debt: Decimal

class CustomerReportResponse(BaseModel):
    total_outstanding_debt: Decimal
    top_debtors: List[CustomerDebt]

# Expense Report
class ExpenseCategoryBreakdown(BaseModel):
    category_id: Optional[int] = None
    category_name: str
    total_amount: Decimal

class ExpenseReportResponse(BaseModel):
    total_expenses: Decimal
    by_category: List[ExpenseCategoryBreakdown]
