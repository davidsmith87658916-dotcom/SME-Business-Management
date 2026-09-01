import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.product import Product, ProductStatusEnum
from app.models.purchase import Purchase, PurchaseStatusEnum
from app.models.purchase_item import PurchaseItem
from app.models.stock_movement import MovementTypeEnum, ReferenceTypeEnum
from app.models.supplier import Supplier
from app.schemas.purchase import PurchaseCreate
from app.services.product_service import record_stock_movement
from app.utils.money import ZERO_MONEY, as_money


def _transaction_time(value: datetime | None) -> datetime:
    if value is None:
        return datetime.now(timezone.utc)
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def create_purchase(db: Session, purchase_data: PurchaseCreate, user_id: int):
    product_ids = [item.product_id for item in purchase_data.items]
    if len(product_ids) != len(set(product_ids)):
        raise HTTPException(status_code=400, detail="A product may appear only once in a purchase")

    try:
        supplier = db.query(Supplier).filter(
            Supplier.id == purchase_data.supplier_id,
            Supplier.business_id == purchase_data.business_id,
        ).first()
        if not supplier:
            raise HTTPException(status_code=400, detail="Supplier not found in this business")

        products = db.query(Product).filter(
            Product.business_id == purchase_data.business_id,
            Product.id.in_(sorted(product_ids)),
        ).order_by(Product.id).with_for_update().all()
        product_map = {int(product.id): product for product in products}
        if len(product_map) != len(product_ids):
            raise HTTPException(status_code=400, detail="One or more products were not found in this business")

        prepared_items: list[dict] = []
        total_amount = ZERO_MONEY
        for item in purchase_data.items:
            product = product_map[item.product_id]
            if product.status != ProductStatusEnum.ACTIVE:
                raise HTTPException(status_code=400, detail=f"Product {product.name} is inactive")
            quantity = as_money(item.quantity)
            cost_price = as_money(item.cost_price)
            subtotal = as_money(cost_price * quantity)
            total_amount = as_money(total_amount + subtotal)
            prepared_items.append(
                {
                    "product": product,
                    "quantity": quantity,
                    "cost_price": cost_price,
                    "subtotal": subtotal,
                }
            )

        paid_amount = as_money(purchase_data.paid_amount)
        if paid_amount > total_amount:
            raise HTTPException(status_code=400, detail="Paid amount cannot exceed purchase total")

        purchase_time = _transaction_time(purchase_data.purchase_date)
        completed_time = datetime.now(timezone.utc)
        invoice_no = purchase_data.invoice_no or f"PUR-{purchase_data.business_id}-{uuid.uuid4().hex[:12].upper()}"
        new_purchase = Purchase(
            business_id=purchase_data.business_id,
            supplier_id=purchase_data.supplier_id,
            invoice_no=invoice_no,
            total_amount=total_amount,
            paid_amount=paid_amount,
            status=PurchaseStatusEnum.COMPLETED,
            purchase_date=purchase_time,
            completed_at=completed_time,
            created_by=user_id,
        )
        db.add(new_purchase)
        db.flush()

        for prepared in prepared_items:
            product = prepared["product"]
            db.add(
                PurchaseItem(
                    purchase_id=new_purchase.id,
                    product_id=product.id,
                    quantity=prepared["quantity"],
                    cost_price=prepared["cost_price"],
                    subtotal=prepared["subtotal"],
                )
            )

            old_stock = as_money(product.stock_qty)
            new_stock = as_money(old_stock + prepared["quantity"])
            if new_stock > 0:
                product.cost_price = as_money(
                    ((old_stock * as_money(product.cost_price)) + prepared["subtotal"]) / new_stock
                )

            record_stock_movement(
                db=db,
                business_id=purchase_data.business_id,
                product_id=int(product.id),
                movement_type=MovementTypeEnum.IN,
                quantity=prepared["quantity"],
                reference_type=ReferenceTypeEnum.PURCHASE,
                reference_id=int(new_purchase.id),
                note=f"Purchase invoice: {invoice_no}",
                commit=False,
            )

        db.commit()
        db.refresh(new_purchase)
        return new_purchase
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Purchase invoice number already exists in this business") from exc
    except Exception:
        db.rollback()
        raise


def get_purchase(db: Session, purchase_id: int, business_id: int):
    return db.query(Purchase).filter(Purchase.id == purchase_id, Purchase.business_id == business_id).first()


def get_purchases(
    db: Session, 
    business_id: int, 
    supplier_id: Optional[int] = None,
    skip: int = 0, 
    limit: int = 100
):
    query = db.query(Purchase).filter(Purchase.business_id == business_id)
    if supplier_id is not None:
        query = query.filter(Purchase.supplier_id == supplier_id)
    return query.order_by(Purchase.purchase_date.desc()).offset(skip).limit(limit).all()
