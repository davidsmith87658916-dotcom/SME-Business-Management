from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.core.dependencies import get_current_user, get_current_user_business, require_business_owner
from app.models.user import User
from app.schemas.business import (
    BusinessCreate, BusinessResponse, BusinessUpdate,
    BusinessMemberCreate, BusinessMemberResponse
)
from app.services import business_service

router = APIRouter()

@router.post("/", response_model=BusinessResponse)
def create_business(business_in: BusinessCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return business_service.create_business(db, business_in, int(current_user.id))

@router.get("/", response_model=List[BusinessResponse])
def get_user_businesses(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return business_service.get_user_businesses(db, int(current_user.id))

@router.put("/{business_id}", response_model=BusinessResponse)
def update_business(business_id: int, update_data: BusinessUpdate, db: Session = Depends(get_db), current_user: User = Depends(require_business_owner)):
    return business_service.update_business(db, business_id, update_data)

@router.post("/{business_id}/members", response_model=BusinessMemberResponse)
def add_business_member(business_id: int, member_data: BusinessMemberCreate, db: Session = Depends(get_db), current_user: User = Depends(require_business_owner)):
    return business_service.add_business_member(db, business_id, member_data)

@router.get("/{business_id}/members", response_model=List[BusinessMemberResponse])
def get_business_members(business_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user_business)):
    return business_service.get_business_members(db, business_id)

@router.delete("/{business_id}/members/{user_id}")
def remove_business_member(business_id: int, user_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user_business)):
    return business_service.remove_business_member(db, business_id, int(current_user.id), user_id)
