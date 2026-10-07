from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.dependencies import get_current_user
from app.schemas.user import UserCreate, UserResponse, UserUpdate
from app.services.user_service import create_user


user_router = APIRouter(prefix="/users", tags=["Users"])

@user_router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user_endpoint(user: UserCreate, db: Session = Depends(get_db)):
    return create_user(db, user)

@user_router.get("/me", response_model=UserResponse)
def get_own_profile(current_user: User = Depends(get_current_user)):
    return current_user

@user_router.patch("/me", response_model=UserResponse)
def update_profile(data: UserUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if data.name is not None:
        current_user.name = data.name
    db.commit()
    db.refresh(current_user)
    return current_user
