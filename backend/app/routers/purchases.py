from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.core.dependencies import get_current_user_business
from app.schemas.purchase import PurchaseCreate, PurchaseResponse
from app.services import purchase_service

router = APIRouter()

@router.post("/{business_id}/purchases", response_model=PurchaseResponse)
def create_purchase(business_id: int, purchase_in: PurchaseCreate, db: Session = Depends(get_db), user = Depends(get_current_user_business)):
    purchase_in.business_id = business_id
    return purchase_service.create_purchase(db, purchase_in, int(user.id))

@router.get("/{business_id}/purchases", response_model=List[PurchaseResponse])
def get_purchases(
    business_id: int, 
    supplier_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db), 
    user = Depends(get_current_user_business)
):
    return purchase_service.get_purchases(db, business_id, supplier_id=supplier_id, skip=skip, limit=limit)

@router.get("/{business_id}/purchases/{purchase_id}", response_model=PurchaseResponse)
def get_purchase(business_id: int, purchase_id: int, db: Session = Depends(get_db), user = Depends(get_current_user_business)):
    purchase = purchase_service.get_purchase(db, purchase_id, business_id)
    if not purchase:
        raise HTTPException(status_code=404, detail="Purchase not found")
    return purchase
