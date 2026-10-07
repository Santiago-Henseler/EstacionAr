from fastapi import HTTPException, status
from app.repositories.user_repository import get_user_by_email, save_user
from app.models.user import User
from pwdlib import PasswordHash
from app.schemas.user import UserCreate


password_hash = PasswordHash.recommended()

def create_user(db, user_data:UserCreate):
    existing_user = get_user_by_email(db,user_data.email)
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="email already exists")
    

    hashed_password = password_hash.hash(user_data.password)

    user = User(name=user_data.name, email= user_data.email,hashed_password = hashed_password)
    

    return save_user(db, user)



