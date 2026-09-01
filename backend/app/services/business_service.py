from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.user import User
from app.models.business import Business
from app.models.business_member import BusinessMember, RoleEnum
from app.schemas.business import BusinessCreate, BusinessUpdate, BusinessMemberCreate

def create_business(db: Session, business_data: BusinessCreate, user_id: int):
    # Create the business
    new_business = Business(
        name=business_data.name,
        phone=business_data.phone,
        address=business_data.address,
        logo=business_data.logo,
        currency=business_data.currency,
        timezone=business_data.timezone
    )
    try:
        db.add(new_business)
        db.flush()

        owner_member = BusinessMember(
            user_id=user_id,
            business_id=new_business.id,
            role=RoleEnum.owner,
        )
        db.add(owner_member)
        db.commit()
        db.refresh(new_business)
        return new_business
    except Exception:
        db.rollback()
        raise

def get_business(db: Session, business_id: int):
    return db.query(Business).filter(Business.id == business_id).first()

def get_user_businesses(db: Session, user_id: int):
    memberships = db.query(BusinessMember).filter(BusinessMember.user_id == user_id).all()
    business_ids = [m.business_id for m in memberships]
    return db.query(Business).filter(Business.id.in_(business_ids)).all()

def verify_business_membership(db: Session, business_id: int, user_id: int):
    member = db.query(BusinessMember).filter(
        BusinessMember.business_id == business_id,
        BusinessMember.user_id == user_id
    ).first()
    if not member:
        raise HTTPException(status_code=403, detail="Not authorized to access this business")
    return member

def update_business(db: Session, business_id: int, update_data: BusinessUpdate):
    business = get_business(db, business_id)
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")
    
    update_dict = update_data.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(business, key, value)
        
    db.commit()
    db.refresh(business)
    return business

def add_business_member(db: Session, business_id: int, member_data: BusinessMemberCreate):
    # Check if user to add exists
    user = db.query(User).filter(User.id == member_data.user_id).first() # type: ignore
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    # Check if already a member
    existing = db.query(BusinessMember).filter(
        BusinessMember.business_id == business_id,
        BusinessMember.user_id == member_data.user_id
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="User is already a member of this business")
        
    new_member = BusinessMember(
        business_id=business_id,
        user_id=member_data.user_id,
        role=member_data.role
    )
    db.add(new_member)
    db.commit()
    db.refresh(new_member)
    return new_member

def get_business_members(db: Session, business_id: int):
    return db.query(BusinessMember).filter(BusinessMember.business_id == business_id).all()

def remove_business_member(db: Session, business_id: int, requester_id: int, user_id_to_remove: int):
    requester = verify_business_membership(db, business_id, requester_id)
    if requester.role != RoleEnum.owner and requester_id != user_id_to_remove:
        raise HTTPException(status_code=403, detail="Not authorized to remove this member")
        
    # Cannot remove the last owner
    if requester.role == RoleEnum.owner and requester_id == user_id_to_remove:
        owner_count = db.query(BusinessMember).filter(
            BusinessMember.business_id == business_id,
            BusinessMember.role == RoleEnum.owner
        ).count()
        if owner_count <= 1:
            raise HTTPException(status_code=400, detail="Cannot remove the only owner of the business")
            
    member = db.query(BusinessMember).filter(
        BusinessMember.business_id == business_id,
        BusinessMember.user_id == user_id_to_remove
    ).first()
    
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
        
    db.delete(member)
    db.commit()
    return {"message": "Member removed successfully"}
