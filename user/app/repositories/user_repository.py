from app.models.user import User
from app.models.refresh_token import RefreshToken
from app.models.password_reset_token import PasswordResetToken

def get_user_by_id(db, user_id: int):
    return db.query(User).filter(User.id == user_id).first()

def get_user_by_email(db, email: str):
    return db.query(User).filter(User.email == email).first()

def get_user_by_google_id(db, google_id: str):
    return db.query(User).filter(User.google_id == google_id).first()

def save_user(db, user: User):
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def delete_user(db, user: User):
    # Los tokens tienen FK a users.id sin cascade: hay que borrarlos antes que al usuario
    db.query(RefreshToken).filter(RefreshToken.user_id == user.id).delete(synchronize_session=False)
    db.query(PasswordResetToken).filter(PasswordResetToken.user_id == user.id).delete(synchronize_session=False)
    db.delete(user)
    db.commit()
