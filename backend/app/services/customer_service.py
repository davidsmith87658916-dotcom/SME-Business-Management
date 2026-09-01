from sqlalchemy.orm import Session
from app.models.customer import Customer
from app.models.sale import Sale
from app.models.debt import Debt, DebtStatusEnum
from app.models.payment import Payment
from fastapi import HTTPException
from app.schemas.customer import CustomerCreate, CustomerUpdate

def create_customer(db: Session, customer_data: CustomerCreate):
    new_customer = Customer(**customer_data.model_dump())
    try:
        db.add(new_customer)
        db.commit()
        db.refresh(new_customer)
        return new_customer
    except Exception:
        db.rollback()
        raise

def get_customers(db: Session, business_id: int, skip: int = 0, limit: int = 100):
    return db.query(Customer).filter(
        Customer.business_id == business_id
    ).order_by(Customer.name.asc()).offset(skip).limit(limit).all()

def get_customer(db: Session, customer_id: int, business_id: int):
    return db.query(Customer).filter(
        Customer.id == customer_id,
        Customer.business_id == business_id
    ).first()

def update_customer(db: Session, business_id: int, customer_id: int, update_data: CustomerUpdate):
    customer = get_customer(db, customer_id, business_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    for key, value in update_data.model_dump(exclude_unset=True).items():
        setattr(customer, key, value)
    try:
        db.commit()
        db.refresh(customer)
        return customer
    except Exception:
        db.rollback()
        raise

def delete_customer(db: Session, business_id: int, customer_id: int):
    customer = get_customer(db, customer_id, business_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    # Prevent deletion if customer has open debts
    open_debts = db.query(Debt).filter(
        Debt.customer_id == customer_id,
        Debt.business_id == business_id,
        Debt.status != DebtStatusEnum.PAID,
    ).count()
    if open_debts > 0:
        raise HTTPException(status_code=409, detail="Cannot delete customer with open debts")
    try:
        db.delete(customer)
        db.commit()
        return {"message": "Customer deleted successfully"}
    except Exception:
        db.rollback()
        raise

def get_customer_history(db: Session, customer_id: int, business_id: int):
    customer = get_customer(db, customer_id, business_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
        
    sales = db.query(Sale).filter(Sale.customer_id == customer_id, Sale.business_id == business_id).order_by(Sale.created_at.desc()).all()
    debts = db.query(Debt).filter(Debt.customer_id == customer_id, Debt.business_id == business_id).order_by(Debt.created_at.desc()).all()
    payments = db.query(Payment).filter(Payment.customer_id == customer_id, Payment.business_id == business_id).order_by(Payment.created_at.desc()).all()
    
    return {
        "sales": sales,
        "debts": debts,
        "payments": payments
    }

