from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.core.dependencies import get_current_user_business
from app.schemas.debt import DebtResponse
from app.models.debt import DebtStatusEnum
from app.schemas.payment import PaymentCreate, PaymentResponse
from app.services import debt_service

router = APIRouter()

@router.get("/{business_id}/debts", response_model=List[DebtResponse])
def get_debts(
    business_id: int, 
    customer_id: Optional[int] = None, 
    status: Optional[DebtStatusEnum] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db), 
    user = Depends(get_current_user_business)
):
    return debt_service.get_debts(db, business_id, customer_id=customer_id, status=status, skip=skip, limit=limit)

@router.get("/{business_id}/debts/{debt_id}", response_model=DebtResponse)
def get_debt(business_id: int, debt_id: int, db: Session = Depends(get_db), user = Depends(get_current_user_business)):
    debt = debt_service.get_debt(db, debt_id, business_id)
    if not debt:
        raise HTTPException(status_code=404, detail="Debt not found")
    return debt

@router.post("/{business_id}/debts/{debt_id}/payments", response_model=PaymentResponse)
def record_payment(business_id: int, debt_id: int, payment_in: PaymentCreate, db: Session = Depends(get_db), user = Depends(get_current_user_business)):
    return debt_service.record_payment(
        db=db,
        business_id=business_id,
        debt_id=debt_id,
        amount=payment_in.amount,
        payment_method=payment_in.payment_method,
        user_id=int(user.id),
        note=payment_in.note,
        payment_date=payment_in.payment_date,
    )
