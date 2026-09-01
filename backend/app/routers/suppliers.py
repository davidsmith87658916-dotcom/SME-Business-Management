from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.core.dependencies import get_current_user_business
from app.schemas.supplier import SupplierCreate, SupplierResponse, SupplierUpdate
from app.services import supplier_service

router = APIRouter()

@router.post("/{business_id}/suppliers", response_model=SupplierResponse)
def create_supplier(business_id: int, supplier_in: SupplierCreate, db: Session = Depends(get_db), user = Depends(get_current_user_business)):
    supplier_in.business_id = business_id
    return supplier_service.create_supplier(db, supplier_in)

@router.get("/{business_id}/suppliers", response_model=List[SupplierResponse])
def get_suppliers(business_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db), user = Depends(get_current_user_business)):
    return supplier_service.get_suppliers(db, business_id, skip=skip, limit=limit)

@router.get("/{business_id}/suppliers/{supplier_id}", response_model=SupplierResponse)
def get_supplier(business_id: int, supplier_id: int, db: Session = Depends(get_db), user = Depends(get_current_user_business)):
    supplier = supplier_service.get_supplier(db, supplier_id, business_id)
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return supplier

@router.put("/{business_id}/suppliers/{supplier_id}", response_model=SupplierResponse)
def update_supplier(business_id: int, supplier_id: int, update_data: SupplierUpdate, db: Session = Depends(get_db), user = Depends(get_current_user_business)):
    return supplier_service.update_supplier(db, business_id, supplier_id, update_data)

@router.delete("/{business_id}/suppliers/{supplier_id}")
def delete_supplier(business_id: int, supplier_id: int, db: Session = Depends(get_db), user = Depends(get_current_user_business)):
    return supplier_service.delete_supplier(db, business_id, supplier_id)
