from pydantic import BaseModel, ConfigDict, Field
from decimal import Decimal
from typing import Optional

class DashboardResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    # Today's metrics (Process Flow: "TODAY'S SALES/PROFIT/EXPENSE")
    today_sales: Decimal = Field(default=Decimal('0'))
    today_expense: Decimal = Field(default=Decimal('0'))
    today_profit: Decimal = Field(default=Decimal('0'))

    # Total Debt (Process Flow: "TOTAL DEBT $2,450 - 5 Customers")
    total_debt: Decimal = Field(default=Decimal('0'))
    debt_customer_count: int = 0

    # Low Stock Items (Process Flow: "LOW STOCK ITEMS 12 - Need attention")
    low_stock_count: int = 0

    # New Orders (Process Flow: "NEW ORDERS 8 - Uncompleted")
    new_orders_count: int = 0

    # Best Seller (Process Flow: "BEST SELLER Latte - 45 Cups")
    best_seller_name: Optional[str] = None
    best_seller_qty: Decimal = Field(default=Decimal('0'))
