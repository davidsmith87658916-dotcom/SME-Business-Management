from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.core.dependencies import get_current_user_business
from app.schemas.customer import CustomerCreate, CustomerResponse, CustomerHistoryResponse, CustomerUpdate
from app.services import customer_service

router = APIRouter()

@router.post("/{business_id}/customers", response_model=CustomerResponse)
def create_customer(business_id: int, customer_in: CustomerCreate, db: Session = Depends(get_db), user = Depends(get_current_user_business)):
    customer_in.business_id = business_id
    return customer_service.create_customer(db, customer_in)

@router.get("/{business_id}/customers", response_model=List[CustomerResponse])
def get_customers(business_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db), user = Depends(get_current_user_business)):
    return customer_service.get_customers(db, business_id, skip=skip, limit=limit)

@router.get("/{business_id}/customers/{customer_id}", response_model=CustomerResponse)
def get_customer(business_id: int, customer_id: int, db: Session = Depends(get_db), user = Depends(get_current_user_business)):
    customer = customer_service.get_customer(db, customer_id, business_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer

@router.put("/{business_id}/customers/{customer_id}", response_model=CustomerResponse)
def update_customer(business_id: int, customer_id: int, update_data: CustomerUpdate, db: Session = Depends(get_db), user = Depends(get_current_user_business)):
    return customer_service.update_customer(db, business_id, customer_id, update_data)

@router.delete("/{business_id}/customers/{customer_id}")
def delete_customer(business_id: int, customer_id: int, db: Session = Depends(get_db), user = Depends(get_current_user_business)):
    return customer_service.delete_customer(db, business_id, customer_id)

@router.get("/{business_id}/customers/{customer_id}/history", response_model=CustomerHistoryResponse)
def get_customer_history(business_id: int, customer_id: int, db: Session = Depends(get_db), user = Depends(get_current_user_business)):
    return customer_service.get_customer_history(db, customer_id, business_id)
