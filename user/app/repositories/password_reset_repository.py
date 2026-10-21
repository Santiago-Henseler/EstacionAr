from datetime import datetime
from sqlalchemy.orm import Session

from app.models.password_reset_token import PasswordResetToken


def create_password_reset_token(
    db: Session,
    user_id: int,
    token_hash: str,
    expires_at: datetime
) -> PasswordResetToken:
    reset_token = PasswordResetToken(
        user_id=user_id,
        token_hash=token_hash,
        expires_at=expires_at,
        used_at=None
    )
    db.add(reset_token)
    db.flush()
    return reset_token


def get_password_reset_token_by_hash(
    db: Session,
    token_hash: str
) -> PasswordResetToken | None:
    return (
        db.query(PasswordResetToken)
        .filter(PasswordResetToken.token_hash == token_hash)
        .first()
    )


def get_active_tokens_by_user_id(
    db: Session,
    user_id: int,
    now: datetime
) -> list[PasswordResetToken]:
    return (
        db.query(PasswordResetToken)
        .filter(
            PasswordResetToken.user_id == user_id,
            PasswordResetToken.used_at.is_(None),
            PasswordResetToken.expires_at > now
        )
        .all()
    )


def invalidate_tokens(tokens: list[PasswordResetToken], used_at: datetime) -> None:
    for token in tokens:
        token.used_at = used_at


def get_other_unused_tokens_by_user_id(
    db: Session,
    user_id: int,
    current_token_id: int
) -> list[PasswordResetToken]:
    return (
        db.query(PasswordResetToken)
        .filter(
            PasswordResetToken.user_id == user_id,
            PasswordResetToken.id != current_token_id,
            PasswordResetToken.used_at.is_(None)
        )
        .all()
    )

def count_recent_tokens_by_user_id(db: Session, user_id: int, since: datetime) -> int:
    return (
        db.query(PasswordResetToken)
        .filter(
            PasswordResetToken.user_id == user_id,
            PasswordResetToken.created_at >= since
        )
        .count()
    )
