from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.customer import Customer
from app.models.debt import Debt, DebtStatusEnum
from app.models.payment import Payment
from app.models.sale import PaymentStatusEnum, Sale
from app.utils.money import as_money


def _transaction_time(value: datetime | None) -> datetime:
    if value is None:
        return datetime.now(timezone.utc)
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def create_debt(
    db: Session,
    business_id: int,
    customer_id: int,
    total_amount: Decimal,
    paid_amount: Decimal,
    sale_id: Optional[int] = None,
    commit: bool = True,
):
    total_amount = as_money(total_amount)
    paid_amount = as_money(paid_amount)
    if paid_amount > total_amount:
        raise HTTPException(status_code=400, detail="Debt paid amount cannot exceed total amount")

    remaining = as_money(total_amount - paid_amount)
    if remaining <= 0:
        return None

    customer = db.query(Customer).filter(
        Customer.id == customer_id,
        Customer.business_id == business_id,
    ).first()
    if not customer:
        raise HTTPException(status_code=400, detail="Customer not found in this business")

    if sale_id is not None:
        sale = db.query(Sale).filter(
            Sale.id == sale_id,
            Sale.business_id == business_id,
            Sale.customer_id == customer_id,
        ).first()
        if not sale:
            raise HTTPException(status_code=400, detail="Sale does not match the debt business and customer")

    debt = Debt(
        business_id=business_id,
        customer_id=customer_id,
        sale_id=sale_id,
        total_amount=total_amount,
        paid_amount=paid_amount,
        remaining_amount=remaining,
        status=DebtStatusEnum.PARTIAL if paid_amount > 0 else DebtStatusEnum.OPEN,
    )
    db.add(debt)
    if commit:
        try:
            db.commit()
            db.refresh(debt)
        except Exception:
            db.rollback()
            raise
    else:
        db.flush()
    return debt


def get_debt(db: Session, debt_id: int, business_id: int):
    return db.query(Debt).filter(Debt.id == debt_id, Debt.business_id == business_id).first()


def get_debts(db: Session, business_id: int, customer_id: Optional[int] = None, status: Optional[DebtStatusEnum] = None, skip: int = 0, limit: int = 100):
    query = db.query(Debt).filter(Debt.business_id == business_id)
    if customer_id is not None:
        query = query.filter(Debt.customer_id == customer_id)
    if status is not None:
        query = query.filter(Debt.status == status)
    return query.order_by(Debt.created_at.desc()).offset(skip).limit(limit).all()


def record_payment(
    db: Session,
    business_id: int,
    debt_id: int,
    amount: Decimal,
    payment_method: str,
    user_id: int,
    note: Optional[str] = None,
    payment_date: Optional[datetime] = None,
):
    amount = as_money(amount)
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Payment amount must be greater than zero")

    try:
        debt = db.query(Debt).filter(
            Debt.id == debt_id,
            Debt.business_id == business_id,
        ).with_for_update().first()
        if not debt:
            raise HTTPException(status_code=404, detail="Debt not found")
        if debt.status == DebtStatusEnum.PAID or debt.remaining_amount <= 0:
            raise HTTPException(status_code=400, detail="Debt is already paid")
        if amount > debt.remaining_amount:
            raise HTTPException(status_code=400, detail="Payment amount exceeds remaining debt")

        transaction_time = _transaction_time(payment_date)
        payment = Payment(
            business_id=business_id,
            debt_id=debt_id,
            sale_id=debt.sale_id,
            customer_id=debt.customer_id,
            amount=amount,
            payment_method=payment_method,
            note=note,
            payment_date=transaction_time,
            created_by=user_id,
        )
        db.add(payment)

        debt.paid_amount = as_money(debt.paid_amount + amount)
        debt.remaining_amount = as_money(debt.total_amount - debt.paid_amount)
        debt.status = DebtStatusEnum.PAID if debt.remaining_amount == 0 else DebtStatusEnum.PARTIAL

        if debt.sale_id is not None:
            sale = db.query(Sale).filter(
                Sale.id == debt.sale_id,
                Sale.business_id == business_id,
            ).with_for_update().first()
            if not sale:
                raise HTTPException(status_code=409, detail="Debt references a missing sale")
            sale.paid_amount = as_money(sale.paid_amount + amount)
            if sale.paid_amount > sale.total_amount:
                raise HTTPException(status_code=409, detail="Sale payment balance would exceed its total")
            sale.payment_status = (
                PaymentStatusEnum.PAID
                if sale.paid_amount == sale.total_amount
                else PaymentStatusEnum.PARTIAL
            )
            if not sale.payment_method:
                sale.payment_method = payment_method

        db.commit()
        db.refresh(payment)
        return payment
    except Exception:
        db.rollback()
        raise
