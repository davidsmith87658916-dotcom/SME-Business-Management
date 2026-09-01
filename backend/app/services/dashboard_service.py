from datetime import datetime, time, timezone
from decimal import Decimal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app.models.business import Business
from app.models.debt import Debt, DebtStatusEnum
from app.models.expense import Expense
from app.models.product import Product, ProductStatusEnum
from app.models.sale import Sale, SaleStatusEnum
from app.models.sale_item import SaleItem
from app.utils.money import ZERO_MONEY


def _business_day_utc(db: Session, business_id: int) -> tuple[datetime, datetime]:
    business = db.query(Business).filter(Business.id == business_id).first()
    timezone_name = business.timezone if business and business.timezone else "UTC"
    try:
        business_timezone = ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError:
        business_timezone = ZoneInfo("UTC")

    local_today = datetime.now(business_timezone).date()
    local_start = datetime.combine(local_today, time.min, tzinfo=business_timezone)
    local_end = datetime.combine(local_today, time.max, tzinfo=business_timezone)
    return local_start.astimezone(timezone.utc), local_end.astimezone(timezone.utc)


def get_dashboard_summary(db: Session, business_id: int):
    today_start, today_end = _business_day_utc(db, business_id)

    completed_today = (
        Sale.business_id == business_id,
        Sale.status == SaleStatusEnum.COMPLETED,
        Sale.sale_date >= today_start,
        Sale.sale_date <= today_end,
    )
    today_sales = db.query(func.sum(Sale.total_amount)).filter(*completed_today).scalar() or ZERO_MONEY
    today_cogs = db.query(func.sum(SaleItem.cost_price * SaleItem.quantity)).join(
        Sale, SaleItem.sale_id == Sale.id
    ).filter(*completed_today).scalar() or ZERO_MONEY
    today_expenses = db.query(func.sum(Expense.amount)).filter(
        Expense.business_id == business_id,
        Expense.expense_date >= today_start,
        Expense.expense_date <= today_end,
    ).scalar() or ZERO_MONEY
    today_profit = today_sales - today_cogs - today_expenses

    total_debt = db.query(func.sum(Debt.remaining_amount)).filter(
        Debt.business_id == business_id,
        Debt.status != DebtStatusEnum.PAID,
        Debt.remaining_amount > 0,
    ).scalar() or ZERO_MONEY
    debt_customer_count = db.query(func.count(func.distinct(Debt.customer_id))).filter(
        Debt.business_id == business_id,
        Debt.status != DebtStatusEnum.PAID,
        Debt.remaining_amount > 0,
    ).scalar() or 0

    low_stock_count = db.query(func.count(Product.id)).filter(
        Product.business_id == business_id,
        Product.status == ProductStatusEnum.ACTIVE,
        Product.stock_qty < 10,
    ).scalar() or 0
    new_orders_count = db.query(func.count(Sale.id)).filter(
        Sale.business_id == business_id,
        Sale.status == SaleStatusEnum.DRAFT,
    ).scalar() or 0

    total_qty = func.sum(SaleItem.quantity).label("total_qty")
    best_seller = db.query(Product.name, total_qty).join(
        SaleItem, Product.id == SaleItem.product_id
    ).join(Sale, SaleItem.sale_id == Sale.id).filter(
        Sale.business_id == business_id,
        Sale.status == SaleStatusEnum.COMPLETED,
    ).group_by(Product.id, Product.name).order_by(desc(total_qty)).first()

    return {
        "today_sales": today_sales,
        "today_expense": today_expenses,
        "today_profit": today_profit,
        "total_debt": total_debt,
        "debt_customer_count": debt_customer_count,
        "low_stock_count": low_stock_count,
        "new_orders_count": new_orders_count,
        "best_seller_name": best_seller.name if best_seller else None,
        "best_seller_qty": best_seller.total_qty if best_seller else Decimal("0"),
    }
