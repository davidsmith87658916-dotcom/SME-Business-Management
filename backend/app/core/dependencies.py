from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from app.config import settings
from app.database import get_db
from app.models.user import User, UserStatusEnum
from app.models.business_member import BusinessMember, RoleEnum
from app.schemas.user import TokenData

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email = payload.get("sub")
        uid = payload.get("uid")
        if not isinstance(email, str) or not email:
            raise credentials_exception
        token_data = TokenData(email=email, user_id=uid)
    except JWTError:
        raise credentials_exception
        
    if token_data.user_id:
        user = db.query(User).filter(User.id == token_data.user_id).first() # type: ignore
    else:
        user = db.query(User).filter(User.email == token_data.email).first() # type: ignore
    if user is None:
        raise credentials_exception
    if user.status != UserStatusEnum.ACTIVE:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")
    return user

def get_current_user_business(
    business_id: int, 
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    member = db.query(BusinessMember).filter(
        BusinessMember.business_id == business_id,
        BusinessMember.user_id == current_user.id
    ).first()
    if not member:
        raise HTTPException(status_code=403, detail="Not authorized to access this business")
    current_user.current_membership = member
    return current_user


def require_business_owner(
    business_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    member = db.query(BusinessMember).filter(
        BusinessMember.business_id == business_id,
        BusinessMember.user_id == current_user.id,
    ).first()
    if not member:
        raise HTTPException(status_code=403, detail="Not authorized to access this business")
    if member.role != RoleEnum.owner:
        raise HTTPException(status_code=403, detail="Only a business owner can perform this action")
    current_user.current_membership = member
    return current_user
