from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.core.dependencies import get_current_user_business, require_business_owner
from app.schemas.product import CategoryCreate, CategoryResponse, CategoryUpdate, ProductCreate, ProductResponse, ProductUpdate, StockAdjustmentCreate, StockMovementResponse
from app.services import product_service

router = APIRouter()

@router.post("/{business_id}/categories", response_model=CategoryResponse)
def create_category(business_id: int, category_in: CategoryCreate, db: Session = Depends(get_db), user = Depends(get_current_user_business)):
    category_in.business_id = business_id
    return product_service.create_category(db, category_in)

@router.get("/{business_id}/categories", response_model=List[CategoryResponse])
def get_categories(business_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db), user = Depends(get_current_user_business)):
    return product_service.get_categories(db, business_id, skip=skip, limit=limit)

@router.get("/{business_id}/categories/{category_id}", response_model=CategoryResponse)
def get_category(business_id: int, category_id: int, db: Session = Depends(get_db), user = Depends(get_current_user_business)):
    category = product_service.get_category(db, category_id, business_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category

@router.put("/{business_id}/categories/{category_id}", response_model=CategoryResponse)
def update_category(business_id: int, category_id: int, update_data: CategoryUpdate, db: Session = Depends(get_db), user = Depends(get_current_user_business)):
    return product_service.update_category(db, business_id, category_id, update_data)

@router.delete("/{business_id}/categories/{category_id}")
def delete_category(business_id: int, category_id: int, db: Session = Depends(get_db), user = Depends(get_current_user_business)):
    return product_service.delete_category(db, business_id, category_id)

@router.post("/{business_id}/products", response_model=ProductResponse)
def create_product(business_id: int, product_in: ProductCreate, db: Session = Depends(get_db), user = Depends(get_current_user_business)):
    product_in.business_id = business_id
    return product_service.create_product(db, product_in)

@router.get("/{business_id}/products", response_model=List[ProductResponse])
def get_products(business_id: int, include_inactive: bool = False, skip: int = 0, limit: int = 100, db: Session = Depends(get_db), user = Depends(get_current_user_business)):
    return product_service.get_products(db, business_id, include_inactive, skip=skip, limit=limit)

@router.get("/{business_id}/products/{product_id}", response_model=ProductResponse)
def get_product(business_id: int, product_id: int, db: Session = Depends(get_db), user = Depends(get_current_user_business)):
    product = product_service.get_product(db, product_id, business_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@router.put("/{business_id}/products/{product_id}", response_model=ProductResponse)
def update_product(business_id: int, product_id: int, product_in: ProductUpdate, db: Session = Depends(get_db), user = Depends(get_current_user_business)):
    return product_service.update_product(db, business_id, product_id, product_in)

@router.delete("/{business_id}/products/{product_id}")
def delete_product(business_id: int, product_id: int, db: Session = Depends(get_db), user = Depends(get_current_user_business)):
    return product_service.delete_product(db, business_id, product_id)

@router.get("/{business_id}/stock-movements", response_model=List[StockMovementResponse])
def get_stock_movements(
    business_id: int, 
    product_id: Optional[int] = None, 
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db), 
    user = Depends(get_current_user_business)
):
    return product_service.get_stock_movements(db, business_id, product_id, skip=skip, limit=limit)


@router.post("/{business_id}/stock-adjustments", response_model=StockMovementResponse)
def adjust_stock(
    business_id: int,
    adjustment_in: StockAdjustmentCreate,
    db: Session = Depends(get_db),
    user = Depends(require_business_owner),
):
    return product_service.adjust_stock(
        db=db,
        business_id=business_id,
        product_id=adjustment_in.product_id,
        quantity=adjustment_in.quantity,
        note=adjustment_in.note,
        user_id=int(user.id),
    )
