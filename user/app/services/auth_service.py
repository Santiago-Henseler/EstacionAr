import hashlib
import secrets
from datetime import datetime, timedelta, UTC
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from pwdlib import PasswordHash
from app.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_DAYS
import jwt

from app.repositories.user_repository import get_user_by_id, get_user_by_email
from app.repositories.refresh_token_repository import (
    create_refresh_token,
    get_refresh_token_by_hash,
    delete_expired_tokens_by_user,
)
from app.schemas.auth import LoginRequest


password_hash = PasswordHash.recommended()


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.now(UTC) + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def _generate_refresh_token(db: Session, user_id: int) -> str:
    delete_expired_tokens_by_user(db, user_id)
    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    expires_at = datetime.now(UTC) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    create_refresh_token(db, user_id=user_id, token_hash=token_hash, expires_at=expires_at)
    return raw_token


def login_user(login_data: LoginRequest, db: Session):
    user = get_user_by_email(db, login_data.email)

    if not user or not user.hashed_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Credentials"
        )

    valid_password = password_hash.verify(
        login_data.password,
        user.hashed_password
    )

    if not valid_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Credentials"
        )

    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    refresh_token = _generate_refresh_token(db, user.id)
    db.commit()

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"  # nosec B105
    }


def refresh_access_token(db: Session, raw_token: str) -> dict:
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    record = get_refresh_token_by_hash(db, token_hash)

    if not record or record.revoked_at is not None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token inválido.")

    if record.expires_at < datetime.now(UTC):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token expirado.")

    user = get_user_by_id(db, record.user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token inválido.")

    record.revoked_at = datetime.now(UTC)

    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    new_refresh_token = _generate_refresh_token(db, user.id)
    db.commit()

    return {"access_token": access_token, "refresh_token": new_refresh_token, "token_type": "bearer"}  # nosec B105
