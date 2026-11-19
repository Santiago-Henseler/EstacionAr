import os
import shutil
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.dependencies import get_current_user
from app.schemas.user import UserCreate, UserResponse, UserUpdate
from app.services.user_service import create_user, delete_user, delete_user_image


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

@user_router.post("/me/picture", response_model=UserResponse)
def upload_profile_picture(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    upload_dir = "uploads/profile_pictures"
    os.makedirs(upload_dir, exist_ok=True)
    extension = os.path.splitext(file.filename or "")[1] or ".jpg"
    filename = f"user_{current_user.id}{extension}"
    file_path = os.path.join(upload_dir, filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    current_user.profile_picture = f"/static/profile_pictures/{filename}"
    db.commit()
    db.refresh(current_user)
    return current_user

@user_router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
def delete_me(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    delete_user(db, current_user)

@user_router.delete("/me/picture", status_code=status.HTTP_204_NO_CONTENT)
def delete_me_picture(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):    
    delete_user_image(db, current_user)

