from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.supplier import Supplier
from app.schemas.supplier import SupplierCreate, SupplierUpdate

def create_supplier(db: Session, supplier_data: SupplierCreate):
    new_supplier = Supplier(**supplier_data.model_dump())
    try:
        db.add(new_supplier)
        db.commit()
        db.refresh(new_supplier)
        return new_supplier
    except Exception:
        db.rollback()
        raise

def get_suppliers(db: Session, business_id: int, skip: int = 0, limit: int = 100):
    return db.query(Supplier).filter(
        Supplier.business_id == business_id
    ).order_by(Supplier.name.asc()).offset(skip).limit(limit).all()

def get_supplier(db: Session, supplier_id: int, business_id: int):
    return db.query(Supplier).filter(
        Supplier.id == supplier_id,
        Supplier.business_id == business_id
    ).first()

def update_supplier(db: Session, business_id: int, supplier_id: int, update_data: SupplierUpdate):
    supplier = get_supplier(db, supplier_id, business_id)
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    for key, value in update_data.model_dump(exclude_unset=True).items():
        setattr(supplier, key, value)
    try:
        db.commit()
        db.refresh(supplier)
        return supplier
    except Exception:
        db.rollback()
        raise

def delete_supplier(db: Session, business_id: int, supplier_id: int):
    supplier = get_supplier(db, supplier_id, business_id)
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    try:
        db.delete(supplier)
        db.commit()
        return {"message": "Supplier deleted successfully"}
    except Exception:
        db.rollback()
        raise

