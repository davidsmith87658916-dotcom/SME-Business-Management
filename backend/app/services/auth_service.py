from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.user import User, UserStatusEnum
from app.schemas.user import UserCreate
from app.security import get_password_hash, verify_password

def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email.strip().lower()).first()

def create_user(db: Session, user_data: UserCreate):
    normalized_email = str(user_data.email).strip().lower()
    db_user = get_user_by_email(db, email=normalized_email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
        
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        name=user_data.name,
        email=normalized_email,
        phone=user_data.phone,
        password=hashed_password,
        status=UserStatusEnum.ACTIVE,
    )
    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user
    except Exception:
        db.rollback()
        raise

def authenticate_user(db: Session, email: str, password: str):
    user = get_user_by_email(db, email)
    if not user:
        # Run a dummy verify to prevent timing attacks for non-existent users
        dummy_hash = "$2b$12$URyusmJ96NPRZnRC6wEf7e76wuV2wKrj6CR/LbnSg891Ksh/Kv0PG"
        verify_password(password, dummy_hash)
        return False
    if not verify_password(password, user.password):
        return False
    if user.status != UserStatusEnum.ACTIVE:
        return False
    return user
