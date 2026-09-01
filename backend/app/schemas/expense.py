from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List
from decimal import Decimal
from datetime import datetime

# ExpenseCategory
class ExpenseCategoryBase(BaseModel):
    name: str

class ExpenseCategoryCreate(ExpenseCategoryBase):
    business_id: int = 0

class ExpenseCategoryUpdate(BaseModel):
    name: Optional[str] = None

class ExpenseCategoryResponse(ExpenseCategoryBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    business_id: int
    created_at: datetime
    updated_at: datetime

# Expense
class ExpenseBase(BaseModel):
    category_id: Optional[int] = None
    title: str
    amount: Decimal = Field(gt=Decimal('0'), max_digits=12, decimal_places=2)
    expense_date: Optional[datetime] = None
    note: Optional[str] = None

class ExpenseCreate(ExpenseBase):
    business_id: int = 0

class ExpenseUpdate(BaseModel):
    category_id: Optional[int] = None
    title: Optional[str] = None
    amount: Optional[Decimal] = Field(default=None, gt=Decimal('0'), max_digits=12, decimal_places=2)
    expense_date: Optional[datetime] = None
    note: Optional[str] = None

class ExpenseResponse(ExpenseBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    business_id: int
    created_at: datetime
    updated_at: datetime

class ExpenseCategoryBreakdown(BaseModel):
    category_id: Optional[int] = None
    category_name: str
    total_amount: Decimal

class ExpenseReportResponse(BaseModel):
    total_expenses: Decimal = Field(default=Decimal('0'))
    by_category: List[ExpenseCategoryBreakdown] = Field(default_factory=list)
