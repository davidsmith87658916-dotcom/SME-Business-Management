from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.core.dependencies import get_current_user_business
from app.schemas.expense import ExpenseCategoryCreate, ExpenseCategoryResponse, ExpenseCategoryUpdate, ExpenseCreate, ExpenseResponse, ExpenseUpdate
from app.services import expense_service

router = APIRouter()

@router.post("/{business_id}/expense-categories", response_model=ExpenseCategoryResponse)
def create_expense_category(business_id: int, category_in: ExpenseCategoryCreate, db: Session = Depends(get_db), user = Depends(get_current_user_business)):
    category_in.business_id = business_id
    return expense_service.create_expense_category(db, category_in)

@router.get("/{business_id}/expense-categories", response_model=List[ExpenseCategoryResponse])
def get_expense_categories(business_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db), user = Depends(get_current_user_business)):
    return expense_service.get_expense_categories(db, business_id, skip=skip, limit=limit)

@router.get("/{business_id}/expense-categories/{category_id}", response_model=ExpenseCategoryResponse)
def get_expense_category(business_id: int, category_id: int, db: Session = Depends(get_db), user = Depends(get_current_user_business)):
    category = expense_service.get_expense_category(db, category_id, business_id)
    if not category:
        raise HTTPException(status_code=404, detail="Expense category not found")
    return category

@router.put("/{business_id}/expense-categories/{category_id}", response_model=ExpenseCategoryResponse)
def update_expense_category(business_id: int, category_id: int, update_data: ExpenseCategoryUpdate, db: Session = Depends(get_db), user = Depends(get_current_user_business)):
    return expense_service.update_expense_category(db, business_id, category_id, update_data)

@router.delete("/{business_id}/expense-categories/{category_id}")
def delete_expense_category(business_id: int, category_id: int, db: Session = Depends(get_db), user = Depends(get_current_user_business)):
    return expense_service.delete_expense_category(db, business_id, category_id)

@router.post("/{business_id}/expenses", response_model=ExpenseResponse)
def create_expense(business_id: int, expense_in: ExpenseCreate, db: Session = Depends(get_db), user = Depends(get_current_user_business)):
    expense_in.business_id = business_id
    return expense_service.create_expense(db, expense_in)

@router.get("/{business_id}/expenses", response_model=List[ExpenseResponse])
def get_expenses(business_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db), user = Depends(get_current_user_business)):
    return expense_service.get_expenses(db, business_id, skip=skip, limit=limit)

@router.get("/{business_id}/expenses/{expense_id}", response_model=ExpenseResponse)
def get_expense(business_id: int, expense_id: int, db: Session = Depends(get_db), user = Depends(get_current_user_business)):
    expense = expense_service.get_expense(db, expense_id, business_id)
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    return expense

@router.put("/{business_id}/expenses/{expense_id}", response_model=ExpenseResponse)
def update_expense(business_id: int, expense_id: int, update_data: ExpenseUpdate, db: Session = Depends(get_db), user = Depends(get_current_user_business)):
    return expense_service.update_expense(db, business_id, expense_id, update_data)

@router.delete("/{business_id}/expenses/{expense_id}")
def delete_expense(business_id: int, expense_id: int, db: Session = Depends(get_db), user = Depends(get_current_user_business)):
    return expense_service.delete_expense(db, business_id, expense_id)

