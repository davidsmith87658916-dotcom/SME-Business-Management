from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException
from app.models.expense_category import ExpenseCategory
from app.models.expense import Expense
from app.schemas.expense import ExpenseCategoryCreate, ExpenseCategoryUpdate, ExpenseCreate, ExpenseUpdate
from app.utils.money import as_money

# ExpenseCategory
def create_expense_category(db: Session, category_data: ExpenseCategoryCreate):
    new_category = ExpenseCategory(**category_data.model_dump())
    db.add(new_category)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Expense category name already exists in this business") from exc
    db.refresh(new_category)
    return new_category

def get_expense_categories(db: Session, business_id: int, skip: int = 0, limit: int = 100):
    return db.query(ExpenseCategory).filter(ExpenseCategory.business_id == business_id).order_by(ExpenseCategory.name.asc()).offset(skip).limit(limit).all()

def get_expense_category(db: Session, category_id: int, business_id: int):
    return db.query(ExpenseCategory).filter(
        ExpenseCategory.id == category_id,
        ExpenseCategory.business_id == business_id
    ).first()

def update_expense_category(db: Session, business_id: int, category_id: int, update_data: ExpenseCategoryUpdate):
    category = get_expense_category(db, category_id, business_id)
    if not category:
        raise HTTPException(status_code=404, detail="Expense category not found")
    for key, value in update_data.model_dump(exclude_unset=True).items():
        setattr(category, key, value)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Expense category name already exists in this business") from exc
    db.refresh(category)
    return category

def delete_expense_category(db: Session, business_id: int, category_id: int):
    category = get_expense_category(db, category_id, business_id)
    if not category:
        raise HTTPException(status_code=404, detail="Expense category not found")
    # Prevent deletion if there are expenses linked
    expenses_count = db.query(Expense).filter(Expense.category_id == category_id, Expense.business_id == business_id).count()
    if expenses_count > 0:
        raise HTTPException(status_code=409, detail="Cannot delete category with associated expenses")
    db.delete(category)
    db.commit()
    return {"message": "Expense category deleted successfully"}

# Expense
def create_expense(db: Session, expense_data: ExpenseCreate):
    if expense_data.category_id is not None:
        category = db.query(ExpenseCategory).filter(
            ExpenseCategory.id == expense_data.category_id,
            ExpenseCategory.business_id == expense_data.business_id,
        ).first()
        if not category:
            raise HTTPException(status_code=400, detail="Expense category not found in this business")

    payload = expense_data.model_dump()
    payload["amount"] = as_money(expense_data.amount)
    new_expense = Expense(**payload)
    try:
        db.add(new_expense)
        db.commit()
        db.refresh(new_expense)
        return new_expense
    except Exception:
        db.rollback()
        raise

def get_expenses(db: Session, business_id: int, skip: int = 0, limit: int = 100):
    return db.query(Expense).filter(Expense.business_id == business_id).order_by(Expense.expense_date.desc()).offset(skip).limit(limit).all()

def get_expense(db: Session, expense_id: int, business_id: int):
    return db.query(Expense).filter(Expense.id == expense_id, Expense.business_id == business_id).first()

def update_expense(db: Session, business_id: int, expense_id: int, update_data: ExpenseUpdate):
    expense = get_expense(db, expense_id, business_id)
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    if update_data.category_id is not None:
        category = get_expense_category(db, update_data.category_id, business_id)
        if not category:
            raise HTTPException(status_code=400, detail="Expense category not found in this business")
    
    update_dict = update_data.model_dump(exclude_unset=True)
    if "amount" in update_dict:
        update_dict["amount"] = as_money(update_dict["amount"])

    for key, value in update_dict.items():
        setattr(expense, key, value)
    
    try:
        db.commit()
        db.refresh(expense)
        return expense
    except Exception:
        db.rollback()
        raise

def delete_expense(db: Session, business_id: int, expense_id: int):
    expense = get_expense(db, expense_id, business_id)
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    try:
        db.delete(expense)
        db.commit()
        return {"message": "Expense deleted successfully"}
    except Exception:
        db.rollback()
        raise

