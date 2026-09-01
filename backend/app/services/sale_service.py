import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.customer import Customer
from app.models.payment import Payment
from app.models.product import Product, ProductStatusEnum
from app.models.sale import PaymentStatusEnum, Sale, SaleStatusEnum
from app.models.sale_item import SaleItem
from app.models.stock_movement import MovementTypeEnum, ReferenceTypeEnum
from app.schemas.sale import SaleComplete, SaleCreate
from app.services.debt_service import create_debt
from app.services.product_service import record_stock_movement
from app.utils.money import ZERO_MONEY, as_money


def _transaction_time(value: datetime | None) -> datetime:
    if value is None:
        return datetime.now(timezone.utc)
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def _payment_status(paid_amount: Decimal, total_amount: Decimal) -> PaymentStatusEnum:
    if paid_amount == total_amount:
        return PaymentStatusEnum.PAID
    if paid_amount > 0:
        return PaymentStatusEnum.PARTIAL
    return PaymentStatusEnum.UNPAID


def create_sale(db: Session, sale_data: SaleCreate, user_id: int):
    product_ids = [item.product_id for item in sale_data.items]
    if len(product_ids) != len(set(product_ids)):
        raise HTTPException(status_code=400, detail="A product may appear only once in a sale")

    try:
        if sale_data.customer_id is not None:
            customer = db.query(Customer).filter(
                Customer.id == sale_data.customer_id,
                Customer.business_id == sale_data.business_id,
            ).first()
            if not customer:
                raise HTTPException(status_code=400, detail="Customer not found in this business")

        products = db.query(Product).filter(
            Product.business_id == sale_data.business_id,
            Product.id.in_(sorted(product_ids)),
        ).order_by(Product.id).with_for_update().all()
        product_map = {int(product.id): product for product in products}
        if len(product_map) != len(product_ids):
            raise HTTPException(status_code=400, detail="One or more products were not found in this business")

        prepared_items: list[dict] = []
        line_total = ZERO_MONEY
        for item in sale_data.items:
            product = product_map[item.product_id]
            if product.status != ProductStatusEnum.ACTIVE:
                raise HTTPException(status_code=400, detail=f"Product {product.name} is inactive")

            quantity = as_money(item.quantity)
            catalog_price = as_money(product.sell_price)
            if item.price is not None and as_money(item.price) != catalog_price:
                raise HTTPException(
                    status_code=400,
                    detail=f"Price for {product.name} does not match the current catalog price",
                )
            if not sale_data.save_as_draft and product.stock_qty < quantity:
                raise HTTPException(
                    status_code=400,
                    detail=f"Insufficient stock for product {product.name}. Current stock: {product.stock_qty}",
                )

            discount = as_money(item.discount)
            gross = as_money(catalog_price * quantity)
            if discount > gross:
                raise HTTPException(status_code=400, detail=f"Discount exceeds line total for {product.name}")
            subtotal = as_money(gross - discount)
            line_total = as_money(line_total + subtotal)
            prepared_items.append(
                {
                    "product": product,
                    "quantity": quantity,
                    "price": catalog_price,
                    "cost_price": as_money(product.cost_price),
                    "discount": discount,
                    "subtotal": subtotal,
                }
            )

        invoice_discount = as_money(sale_data.discount_amount)
        if invoice_discount > line_total:
            raise HTTPException(status_code=400, detail="Invoice discount cannot exceed the items total")

        final_total = as_money(line_total - invoice_discount)
        paid_amount = as_money(sale_data.paid_amount)
        if sale_data.save_as_draft and paid_amount != ZERO_MONEY:
            raise HTTPException(status_code=400, detail="A draft sale cannot contain a payment")
        if not sale_data.save_as_draft and paid_amount > final_total:
            raise HTTPException(status_code=400, detail="Paid amount cannot exceed sale total")
        if not sale_data.save_as_draft and paid_amount < final_total and sale_data.customer_id is None:
            raise HTTPException(status_code=400, detail="Customer is required for an unpaid or partial sale")

        sale_time = _transaction_time(sale_data.sale_date)
        invoice_no = sale_data.invoice_no or f"INV-{sale_data.business_id}-{uuid.uuid4().hex[:12].upper()}"
        sale_status = SaleStatusEnum.DRAFT if sale_data.save_as_draft else SaleStatusEnum.COMPLETED
        payment_status = PaymentStatusEnum.UNPAID if sale_data.save_as_draft else _payment_status(paid_amount, final_total)

        new_sale = Sale(
            business_id=sale_data.business_id,
            customer_id=sale_data.customer_id,
            invoice_no=invoice_no,
            total_amount=final_total,
            discount_amount=invoice_discount,
            paid_amount=paid_amount,
            status=sale_status,
            payment_status=payment_status,
            payment_method=(sale_data.payment_method or "CASH") if paid_amount > ZERO_MONEY else None,
            sale_date=sale_time,
            completed_at=None if sale_data.save_as_draft else datetime.now(timezone.utc),
            created_by=user_id,
        )
        db.add(new_sale)
        db.flush()

        for prepared in prepared_items:
            product = prepared["product"]
            db.add(
                SaleItem(
                    sale_id=new_sale.id,
                    product_id=product.id,
                    quantity=prepared["quantity"],
                    price=prepared["price"],
                    cost_price=prepared["cost_price"],
                    discount=prepared["discount"],
                    subtotal=prepared["subtotal"],
                )
            )
            if not sale_data.save_as_draft:
                record_stock_movement(
                    db=db,
                    business_id=sale_data.business_id,
                    product_id=int(product.id),
                    movement_type=MovementTypeEnum.OUT,
                    quantity=prepared["quantity"],
                    reference_type=ReferenceTypeEnum.SALE,
                    reference_id=int(new_sale.id),
                    note=f"Sale invoice: {invoice_no}",
                    commit=False,
                )

        debt = None
        if not sale_data.save_as_draft and payment_status != PaymentStatusEnum.PAID:
            customer_id = sale_data.customer_id
            if customer_id is None:
                raise HTTPException(
                    status_code=400,
                    detail="Customer is required before a debt can be created",
                )
            debt = create_debt(
                db=db,
                business_id=sale_data.business_id,
                customer_id=customer_id,
                total_amount=final_total,
                paid_amount=paid_amount,
                sale_id=int(new_sale.id),
                commit=False,
            )

        if not sale_data.save_as_draft and paid_amount > 0:
            db.add(
                Payment(
                    business_id=sale_data.business_id,
                    debt_id=int(debt.id) if debt else None,
                    sale_id=int(new_sale.id),
                    customer_id=sale_data.customer_id,
                    amount=paid_amount,
                    payment_method=sale_data.payment_method or "CASH",
                    payment_date=sale_time,
                    note=f"Initial payment for sale invoice: {invoice_no}",
                    created_by=user_id,
                )
            )

        db.commit()
        db.refresh(new_sale)
        return new_sale
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Invoice number already exists in this business") from exc
    except Exception:
        db.rollback()
        raise


def complete_sale(
    db: Session,
    business_id: int,
    sale_id: int,
    completion: SaleComplete,
    user_id: int,
):
    try:
        sale = db.query(Sale).filter(
            Sale.id == sale_id,
            Sale.business_id == business_id,
        ).with_for_update().first()
        if not sale:
            raise HTTPException(status_code=404, detail="Sale not found")
        if sale.status != SaleStatusEnum.DRAFT:
            raise HTTPException(status_code=409, detail="Only a draft sale can be completed")

        sale_items = list(sale.items)
        if not sale_items or any(item.product_id is None for item in sale_items):
            raise HTTPException(status_code=409, detail="Draft sale contains a missing product")

        product_ids = sorted(int(item.product_id) for item in sale_items)
        products = db.query(Product).filter(
            Product.business_id == business_id,
            Product.id.in_(product_ids),
        ).order_by(Product.id).with_for_update().all()
        product_map = {int(product.id): product for product in products}
        if len(product_map) != len(product_ids):
            raise HTTPException(status_code=409, detail="One or more draft products no longer exist in this business")

        for item in sale_items:
            product = product_map[int(item.product_id)]
            quantity = as_money(item.quantity)
            if product.status != ProductStatusEnum.ACTIVE:
                raise HTTPException(status_code=400, detail=f"Product {product.name} is inactive")
            if product.stock_qty < quantity:
                raise HTTPException(
                    status_code=400,
                    detail=f"Insufficient stock for product {product.name}. Current stock: {product.stock_qty}",
                )

        total_amount = as_money(sale.total_amount)
        paid_amount = as_money(completion.paid_amount)
        if paid_amount > total_amount:
            raise HTTPException(status_code=400, detail="Paid amount cannot exceed sale total")
        if paid_amount < total_amount and sale.customer_id is None:
            raise HTTPException(status_code=400, detail="Customer is required for an unpaid or partial sale")

        sale_time = _transaction_time(completion.sale_date)
        payment_status = _payment_status(paid_amount, total_amount)
        sale.status = SaleStatusEnum.COMPLETED
        sale.payment_status = payment_status
        sale.paid_amount = paid_amount
        sale.payment_method = (completion.payment_method or "CASH") if paid_amount > ZERO_MONEY else None
        sale.sale_date = sale_time
        sale.completed_at = datetime.now(timezone.utc)

        for item in sale_items:
            record_stock_movement(
                db=db,
                business_id=business_id,
                product_id=int(item.product_id),
                movement_type=MovementTypeEnum.OUT,
                quantity=as_money(item.quantity),
                reference_type=ReferenceTypeEnum.SALE,
                reference_id=int(sale.id),
                note=f"Completed sale invoice: {sale.invoice_no}",
                commit=False,
            )

        debt = None
        if payment_status != PaymentStatusEnum.PAID:
            debt = create_debt(
                db=db,
                business_id=business_id,
                customer_id=int(sale.customer_id),
                total_amount=total_amount,
                paid_amount=paid_amount,
                sale_id=int(sale.id),
                commit=False,
            )

        if paid_amount > ZERO_MONEY:
            db.add(
                Payment(
                    business_id=business_id,
                    debt_id=int(debt.id) if debt else None,
                    sale_id=int(sale.id),
                    customer_id=sale.customer_id,
                    amount=paid_amount,
                    payment_method=completion.payment_method or "CASH",
                    payment_date=sale_time,
                    note=f"Initial payment for completed sale invoice: {sale.invoice_no}",
                    created_by=user_id,
                )
            )

        db.commit()
        db.refresh(sale)
        return sale
    except Exception:
        db.rollback()
        raise


def get_sale(db: Session, sale_id: int, business_id: int):
    return db.query(Sale).filter(Sale.id == sale_id, Sale.business_id == business_id).first()


def get_sales(
    db: Session, 
    business_id: int, 
    status: Optional[SaleStatusEnum] = None,
    customer_id: Optional[int] = None,
    skip: int = 0, 
    limit: int = 100
):
    query = db.query(Sale).filter(Sale.business_id == business_id)
    if status is not None:
        query = query.filter(Sale.status == status)
    if customer_id is not None:
        query = query.filter(Sale.customer_id == customer_id)
    return query.order_by(Sale.sale_date.desc()).offset(skip).limit(limit).all()
