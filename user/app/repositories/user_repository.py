from app.models.user import User

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
