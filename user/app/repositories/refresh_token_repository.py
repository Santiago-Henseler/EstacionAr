from datetime import datetime, UTC
from sqlalchemy.orm import Session
from app.models.refresh_token import RefreshToken


def create_refresh_token(db: Session, user_id: int, token_hash: str, expires_at: datetime) -> RefreshToken:
    record = RefreshToken(user_id=user_id, token_hash=token_hash, expires_at=expires_at)
    db.add(record)
    return record


def get_refresh_token_by_hash(db: Session, token_hash: str) -> RefreshToken | None:
    return db.query(RefreshToken).filter(RefreshToken.token_hash == token_hash).first()


def delete_expired_tokens_by_user(db: Session, user_id: int) -> None:
    now = datetime.now(UTC)
    db.query(RefreshToken).filter(
        RefreshToken.user_id == user_id,
        RefreshToken.expires_at < now,
    ).delete()
