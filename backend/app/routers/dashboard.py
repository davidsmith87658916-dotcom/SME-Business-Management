from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.core.dependencies import get_current_user_business
from app.schemas.dashboard import DashboardResponse
from app.services import dashboard_service

router = APIRouter()

@router.get("/{business_id}/dashboard", response_model=DashboardResponse)
def get_dashboard(business_id: int, db: Session = Depends(get_db), user = Depends(get_current_user_business)):
    return dashboard_service.get_dashboard_summary(db, business_id)
