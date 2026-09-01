from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.core.dependencies import get_current_user_business
from app.schemas.sale import SaleComplete, SaleCreate, SaleResponse
from app.models.sale import SaleStatusEnum
from app.services import sale_service

router = APIRouter()

@router.post("/{business_id}/sales", response_model=SaleResponse)
def create_sale(business_id: int, sale_in: SaleCreate, db: Session = Depends(get_db), user = Depends(get_current_user_business)):
    sale_in.business_id = business_id
    return sale_service.create_sale(db, sale_in, int(user.id))


@router.post("/{business_id}/sales/{sale_id}/complete", response_model=SaleResponse)
def complete_sale(
    business_id: int,
    sale_id: int,
    completion: SaleComplete,
    db: Session = Depends(get_db),
    user = Depends(get_current_user_business),
):
    return sale_service.complete_sale(db, business_id, sale_id, completion, int(user.id))


@router.get("/{business_id}/sales", response_model=List[SaleResponse])
def get_sales(
    business_id: int, 
    status: Optional[SaleStatusEnum] = None,
    customer_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db), 
    user = Depends(get_current_user_business)
):
    return sale_service.get_sales(db, business_id, status=status, customer_id=customer_id, skip=skip, limit=limit)

@router.get("/{business_id}/sales/{sale_id}", response_model=SaleResponse)
def get_sale(business_id: int, sale_id: int, db: Session = Depends(get_db), user = Depends(get_current_user_business)):
    sale = sale_service.get_sale(db, sale_id, business_id)
    if not sale:
        raise HTTPException(status_code=404, detail="Sale not found")
    return sale
