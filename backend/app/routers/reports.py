from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from app.database import get_db
from app.core.dependencies import get_current_user_business
from app.schemas.report import (
    SalesReportResponse,
    ProfitReportResponse,
    InventoryReportResponse,
    CustomerReportResponse,
    ExpenseReportResponse
)
from app.services import report_service

router = APIRouter()

@router.get("/{business_id}/reports/sales", response_model=SalesReportResponse)
def get_sales_report(
    business_id: int, 
    start_date: Optional[datetime] = Query(None), 
    end_date: Optional[datetime] = Query(None), 
    db: Session = Depends(get_db), 
    user = Depends(get_current_user_business)
):
    return report_service.get_sales_report(db, business_id, start_date, end_date)

@router.get("/{business_id}/reports/profit", response_model=ProfitReportResponse)
def get_profit_report(
    business_id: int, 
    start_date: Optional[datetime] = Query(None), 
    end_date: Optional[datetime] = Query(None), 
    db: Session = Depends(get_db), 
    user = Depends(get_current_user_business)
):
    return report_service.get_profit_report(db, business_id, start_date, end_date)

@router.get("/{business_id}/reports/inventory", response_model=InventoryReportResponse)
def get_inventory_report(
    business_id: int, 
    db: Session = Depends(get_db), 
    user = Depends(get_current_user_business)
):
    return report_service.get_inventory_report(db, business_id)

@router.get("/{business_id}/reports/customers", response_model=CustomerReportResponse)
def get_customer_report(
    business_id: int, 
    db: Session = Depends(get_db), 
    user = Depends(get_current_user_business)
):
    return report_service.get_customer_report(db, business_id)

@router.get("/{business_id}/reports/expenses", response_model=ExpenseReportResponse)
def get_expense_report(
    business_id: int, 
    start_date: Optional[datetime] = Query(None), 
    end_date: Optional[datetime] = Query(None), 
    db: Session = Depends(get_db), 
    user = Depends(get_current_user_business)
):
    return report_service.get_expense_report(db, business_id, start_date, end_date)
