from decimal import Decimal
from typing import Optional

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.category import Category
from app.models.product import Product, ProductStatusEnum
from app.models.stock_movement import MovementTypeEnum, ReferenceTypeEnum, StockMovement
from app.schemas.product import CategoryCreate, CategoryUpdate, ProductCreate, ProductUpdate
from app.utils.money import as_money


def _commit_or_conflict(db: Session, detail: str) -> None:
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail=detail) from exc


def create_category(db: Session, category_data: CategoryCreate):
    new_category = Category(**category_data.model_dump())
    db.add(new_category)
    _commit_or_conflict(db, "A category with this name already exists in the business")
    db.refresh(new_category)
    return new_category


def get_categories(db: Session, business_id: int, skip: int = 0, limit: int = 100):
    return db.query(Category).filter(Category.business_id == business_id).order_by(Category.name.asc()).offset(skip).limit(limit).all()

def get_category(db: Session, category_id: int, business_id: int):
    return db.query(Category).filter(
        Category.id == category_id,
        Category.business_id == business_id
    ).first()

def update_category(db: Session, business_id: int, category_id: int, update_data: CategoryUpdate):
    category = get_category(db, category_id, business_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    for key, value in update_data.model_dump(exclude_unset=True).items():
        setattr(category, key, value)
    _commit_or_conflict(db, "A category with this name already exists in the business")
    db.refresh(category)
    return category

def delete_category(db: Session, business_id: int, category_id: int):
    category = get_category(db, category_id, business_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    # Prevent deletion if products use this category
    product_count = db.query(Product).filter(Product.category_id == category_id, Product.business_id == business_id).count()
    if product_count > 0:
        raise HTTPException(status_code=409, detail="Cannot delete category with associated products")
    db.delete(category)
    db.commit()
    return {"message": "Category deleted successfully"}


def create_product(db: Session, product_data: ProductCreate):
    if product_data.category_id is not None:
        category = db.query(Category).filter(
            Category.id == product_data.category_id,
            Category.business_id == product_data.business_id,
        ).first()
        if not category:
            raise HTTPException(status_code=400, detail="Category not found in this business")

    opening_stock = as_money(product_data.stock_qty)
    payload = product_data.model_dump(exclude={"stock_qty"})
    new_product = Product(**payload, stock_qty=Decimal("0.00"))

    try:
        db.add(new_product)
        db.flush()
        if opening_stock > 0:
            record_stock_movement(
                db=db,
                business_id=product_data.business_id,
                product_id=int(new_product.id),
                movement_type=MovementTypeEnum.ADJUST,
                quantity=opening_stock,
                reference_type=ReferenceTypeEnum.ADJUST,
                reference_id=int(new_product.id),
                note="Opening stock",
                commit=False,
            )
        db.commit()
        db.refresh(new_product)
        return new_product
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="SKU or barcode already exists in this business") from exc
    except Exception:
        db.rollback()
        raise


def get_products(db: Session, business_id: int, include_inactive: bool = False, skip: int = 0, limit: int = 100):
    query = db.query(Product).filter(Product.business_id == business_id)
    if not include_inactive:
        query = query.filter(Product.status == ProductStatusEnum.ACTIVE)
    return query.order_by(Product.name.asc()).offset(skip).limit(limit).all()


def get_product(db: Session, product_id: int, business_id: int, for_update: bool = False):
    query = db.query(Product).filter(
        Product.id == product_id,
        Product.business_id == business_id,
    )
    if for_update:
        query = query.with_for_update()
    return query.first()


def update_product(db: Session, business_id: int, product_id: int, update_data: ProductUpdate):
    product = get_product(db, product_id, business_id, for_update=True)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    if update_data.category_id is not None:
        category = db.query(Category).filter(
            Category.id == update_data.category_id,
            Category.business_id == business_id,
        ).first()
        if not category:
            raise HTTPException(status_code=400, detail="Category not found in this business")

    for key, value in update_data.model_dump(exclude_unset=True).items():
        setattr(product, key, value)

    _commit_or_conflict(db, "SKU or barcode already exists in this business")
    db.refresh(product)
    return product


def delete_product(db: Session, business_id: int, product_id: int):
    product = get_product(db, product_id, business_id, for_update=True)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    product.status = ProductStatusEnum.INACTIVE
    db.commit()
    return {"message": "Product deactivated successfully"}


def record_stock_movement(
    db: Session,
    business_id: int,
    product_id: int,
    movement_type: MovementTypeEnum,
    quantity: Decimal,
    reference_type: Optional[ReferenceTypeEnum] = None,
    reference_id: Optional[int] = None,
    note: str = "",
    commit: bool = True,
):
    quantity = as_money(quantity)
    if movement_type == MovementTypeEnum.ADJUST:
        if quantity == 0:
            raise HTTPException(status_code=400, detail="Stock adjustment cannot be zero")
        delta = quantity
    else:
        if quantity <= 0:
            raise HTTPException(status_code=400, detail="Stock movement quantity must be greater than zero")
        delta = -quantity if movement_type == MovementTypeEnum.OUT else quantity

    product = get_product(db, product_id, business_id, for_update=True)
    if not product:
        raise HTTPException(status_code=404, detail=f"Product {product_id} not found in this business")
    if product.status != ProductStatusEnum.ACTIVE and movement_type != MovementTypeEnum.ADJUST:
        raise HTTPException(status_code=400, detail=f"Product {product.name} is inactive")

    next_stock = as_money(product.stock_qty + delta)
    if next_stock < 0:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient stock for product {product.name}. Current stock: {product.stock_qty}",
        )

    movement = StockMovement(
        business_id=business_id,
        product_id=product_id,
        type=movement_type,
        quantity=quantity,
        reference_type=reference_type,
        reference_id=reference_id,
        note=note,
    )
    db.add(movement)
    product.stock_qty = next_stock

    if commit:
        try:
            db.commit()
            db.refresh(movement)
        except Exception:
            db.rollback()
            raise
    return movement


def adjust_stock(
    db: Session,
    business_id: int,
    product_id: int,
    quantity: Decimal,
    note: str,
    user_id: int,
):
    return record_stock_movement(
        db=db,
        business_id=business_id,
        product_id=product_id,
        movement_type=MovementTypeEnum.ADJUST,
        quantity=quantity,
        reference_type=ReferenceTypeEnum.ADJUST,
        reference_id=user_id,
        note=note,
        commit=True,
    )


def get_stock_movements(db: Session, business_id: int, product_id: Optional[int] = None, skip: int = 0, limit: int = 100):
    query = db.query(StockMovement).filter(StockMovement.business_id == business_id)
    if product_id is not None:
        query = query.filter(StockMovement.product_id == product_id)
    return query.order_by(StockMovement.created_at.desc()).offset(skip).limit(limit).all()
