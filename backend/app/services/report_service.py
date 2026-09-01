from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import HTTPException
from sqlalchemy import and_, case, desc, func
from sqlalchemy.orm import Session

from app.models.business import Business
from app.models.customer import Customer
from app.models.debt import Debt, DebtStatusEnum
from app.models.expense import Expense
from app.models.expense_category import ExpenseCategory
from app.models.product import Product, ProductStatusEnum
from app.models.sale import Sale, SaleStatusEnum
from app.models.sale_item import SaleItem
from app.utils.money import ZERO_MONEY


def _normalize_period(
    db: Session,
    business_id: int,
    start_date: Optional[datetime],
    end_date: Optional[datetime],
) -> tuple[Optional[datetime], Optional[datetime]]:
    business = db.query(Business).filter(Business.id == business_id).first()
    try:
        business_timezone = ZoneInfo(business.timezone if business and business.timezone else "UTC")
    except ZoneInfoNotFoundError:
        business_timezone = ZoneInfo("UTC")

    def to_utc(value: Optional[datetime]) -> Optional[datetime]:
        if value is None:
            return None
        if value.tzinfo is None:
            value = value.replace(tzinfo=business_timezone)
        return value.astimezone(timezone.utc)

    normalized_start = to_utc(start_date)
    normalized_end = to_utc(end_date)
    if normalized_start and normalized_end and normalized_start > normalized_end:
        raise HTTPException(status_code=400, detail="start_date must be before or equal to end_date")
    return normalized_start, normalized_end


def _completed_sales_query(db: Session, business_id: int, start_date=None, end_date=None):
    query = db.query(Sale).filter(
        Sale.business_id == business_id,
        Sale.status == SaleStatusEnum.COMPLETED,
    )
    if start_date:
        query = query.filter(Sale.sale_date >= start_date)
    if end_date:
        query = query.filter(Sale.sale_date <= end_date)
    return query


def get_sales_report(db: Session, business_id: int, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None):
    start_date, end_date = _normalize_period(db, business_id, start_date, end_date)
    query = _completed_sales_query(db, business_id, start_date, end_date)
    total_sales = query.with_entities(func.sum(Sale.total_amount)).scalar() or ZERO_MONEY
    total_transactions = query.count()

    sale_gross = db.query(
        SaleItem.sale_id.label("sale_id"),
        func.sum(SaleItem.subtotal).label("gross_total"),
    ).group_by(SaleItem.sale_id).subquery()

    adjusted_revenue = case(
        (
            sale_gross.c.gross_total > 0,
            SaleItem.subtotal
            - (Sale.discount_amount * SaleItem.subtotal / sale_gross.c.gross_total),
        ),
        else_=Decimal("0"),
    )
    total_quantity_sold = func.sum(SaleItem.quantity).label("total_quantity_sold")
    total_revenue = func.sum(adjusted_revenue).label("total_revenue")
    item_query = db.query(
        SaleItem.product_id,
        Product.name.label("product_name"),
        total_quantity_sold,
        total_revenue,
    ).join(Sale, SaleItem.sale_id == Sale.id).join(
        sale_gross, SaleItem.sale_id == sale_gross.c.sale_id
    ).outerjoin(Product, SaleItem.product_id == Product.id).filter(
        Sale.business_id == business_id,
        Sale.status == SaleStatusEnum.COMPLETED,
    )
    if start_date:
        item_query = item_query.filter(Sale.sale_date >= start_date)
    if end_date:
        item_query = item_query.filter(Sale.sale_date <= end_date)

    rows = item_query.group_by(SaleItem.product_id, Product.name).order_by(desc(total_quantity_sold)).limit(10).all()
    return {
        "total_sales_amount": total_sales,
        "total_transactions": total_transactions,
        "top_selling_products": [
            {
                "product_id": row.product_id,
                "product_name": row.product_name or "Unknown Product",
                "total_quantity_sold": row.total_quantity_sold,
                "total_revenue": row.total_revenue,
            }
            for row in rows
        ],
    }


def get_profit_report(db: Session, business_id: int, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None):
    start_date, end_date = _normalize_period(db, business_id, start_date, end_date)
    sales_query = _completed_sales_query(db, business_id, start_date, end_date)
    total_sales = sales_query.with_entities(func.sum(Sale.total_amount)).scalar() or ZERO_MONEY

    cogs_query = db.query(func.sum(SaleItem.cost_price * SaleItem.quantity)).join(
        Sale, SaleItem.sale_id == Sale.id
    ).filter(
        Sale.business_id == business_id,
        Sale.status == SaleStatusEnum.COMPLETED,
    )
    if start_date:
        cogs_query = cogs_query.filter(Sale.sale_date >= start_date)
    if end_date:
        cogs_query = cogs_query.filter(Sale.sale_date <= end_date)
    total_cogs = cogs_query.scalar() or ZERO_MONEY

    expense_query = db.query(func.sum(Expense.amount)).filter(Expense.business_id == business_id)
    if start_date:
        expense_query = expense_query.filter(Expense.expense_date >= start_date)
    if end_date:
        expense_query = expense_query.filter(Expense.expense_date <= end_date)
    total_expenses = expense_query.scalar() or ZERO_MONEY

    return {
        "total_sales": total_sales,
        "total_cogs": total_cogs,
        "total_expenses": total_expenses,
        "net_profit": total_sales - total_cogs - total_expenses,
    }


def get_inventory_report(db: Session, business_id: int):
    active_filter = (
        Product.business_id == business_id,
        Product.status == ProductStatusEnum.ACTIVE,
    )
    total_value = db.query(func.sum(Product.stock_qty * Product.cost_price)).filter(*active_filter).scalar() or ZERO_MONEY
    total_products = db.query(Product).filter(*active_filter).count()
    low_stock = db.query(Product).filter(
        *active_filter,
        Product.stock_qty < 10,
    ).order_by(Product.stock_qty.asc()).limit(10).all()
    return {
        "total_stock_value": total_value,
        "total_products_count": total_products,
        "low_stock_items": [
            {
                "product_id": int(product.id),
                "product_name": product.name,
                "current_stock": product.stock_qty,
                "cost_price": product.cost_price,
            }
            for product in low_stock
        ],
    }


def get_customer_report(db: Session, business_id: int):
    total_debt = db.query(func.sum(Debt.remaining_amount)).filter(
        Debt.business_id == business_id,
        Debt.status != DebtStatusEnum.PAID,
        Debt.remaining_amount > 0,
    ).scalar() or ZERO_MONEY

    total_by_customer = func.sum(Debt.remaining_amount).label("total_debt")
    rows = db.query(
        Debt.customer_id,
        Customer.name,
        total_by_customer,
    ).join(
        Customer,
        and_(Debt.customer_id == Customer.id, Customer.business_id == business_id),
    ).filter(
        Debt.business_id == business_id,
        Debt.status != DebtStatusEnum.PAID,
        Debt.remaining_amount > 0,
    ).group_by(Debt.customer_id, Customer.name).order_by(desc(total_by_customer)).limit(10).all()

    return {
        "total_outstanding_debt": total_debt,
        "top_debtors": [
            {
                "customer_id": row.customer_id,
                "customer_name": row.name,
                "total_debt": row.total_debt,
            }
            for row in rows
        ],
    }


def get_expense_report(db: Session, business_id: int, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None):
    start_date, end_date = _normalize_period(db, business_id, start_date, end_date)
    query = db.query(Expense).filter(Expense.business_id == business_id)
    if start_date:
        query = query.filter(Expense.expense_date >= start_date)
    if end_date:
        query = query.filter(Expense.expense_date <= end_date)
    total_amount = query.with_entities(func.sum(Expense.amount)).scalar() or ZERO_MONEY

    total_by_category = func.sum(Expense.amount).label("total_amount")
    join_query = db.query(
        Expense.category_id,
        ExpenseCategory.name,
        total_by_category,
    ).outerjoin(
        ExpenseCategory,
        and_(Expense.category_id == ExpenseCategory.id, ExpenseCategory.business_id == business_id),
    ).filter(Expense.business_id == business_id)
    if start_date:
        join_query = join_query.filter(Expense.expense_date >= start_date)
    if end_date:
        join_query = join_query.filter(Expense.expense_date <= end_date)
    rows = join_query.group_by(Expense.category_id, ExpenseCategory.name).all()

    return {
        "total_expenses": total_amount,
        "by_category": [
            {
                "category_id": row.category_id,
                "category_name": row.name or "Uncategorized",
                "total_amount": row.total_amount,
            }
            for row in rows
        ],
    }
