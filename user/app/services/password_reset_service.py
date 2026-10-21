from datetime import datetime, timedelta, UTC
import hashlib
import logging
import secrets
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from pwdlib import PasswordHash
from app.config import RESET_TOKEN_EXPIRATION_MINUTES
from app.config import API_BASE_URL
from app.config import SENDGRID_API_KEY
from app.config import SENDGRID_FROM_EMAIL
from app.config import RESET_MAX_ATTEMPTS
from app.config import RESET_WINDOW_MINUTES
from app.repositories.user_repository import get_user_by_email, get_user_by_id
from app.repositories.refresh_token_repository import revoke_tokens_by_user
from app.repositories.password_reset_repository import (
    create_password_reset_token,
    get_password_reset_token_by_hash,
    get_active_tokens_by_user_id,
    invalidate_tokens,
    get_other_unused_tokens_by_user_id,
    count_recent_tokens_by_user_id
)

password_hash = PasswordHash.recommended()
logger = logging.getLogger(__name__)


def generate_reset_token() -> str:
    return secrets.token_urlsafe(32)


def hash_reset_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def get_reset_token_expiration() -> datetime:
    return datetime.now(UTC) + timedelta(minutes=RESET_TOKEN_EXPIRATION_MINUTES)


def build_reset_link(token: str) -> str:
    return f"{API_BASE_URL}/auth/reset-password/redirect?token={token}"


def send_reset_email(email: str, reset_link: str) -> None:
    message = Mail(
        from_email=SENDGRID_FROM_EMAIL,
        to_emails=email,
        subject="Recupero de contraseña",
        html_content=f"<p>Usá este enlace para resetear tu contraseña:</p><a href='{reset_link}'>{reset_link}</a>",
    )
    SendGridAPIClient(SENDGRID_API_KEY).send(message)



def request_password_reset(db: Session, email: str) -> dict:
    generic_response = {
        "message": "Si el email está registrado, se enviará un enlace de recuperación."
    }

    user = get_user_by_email(db, email)

    if not user:
        logger.info(
            "Solicitud de reset para email no registrado",
            extra={"event": "password_reset_requested_unknown_email"},
        )
        return generic_response

    now = datetime.now(UTC)

    window_start = now - timedelta(minutes=RESET_WINDOW_MINUTES)
    recent_count = count_recent_tokens_by_user_id(db, user.id, window_start)
    if recent_count >= RESET_MAX_ATTEMPTS:
        logger.warning(
            "Solicitud de reset rechazada por rate limit de cuenta",
            extra={"event": "password_reset_rate_limited", "user_id": user.id},
        )
        return generic_response


    active_tokens = get_active_tokens_by_user_id(db, user.id, now)
    invalidate_tokens(active_tokens, now)

    raw_token = generate_reset_token()
    token_hash = hash_reset_token(raw_token)
    expires_at = get_reset_token_expiration()

    create_password_reset_token(
        db=db,
        user_id=user.id,
        token_hash=token_hash,
        expires_at=expires_at
    )

    reset_link = build_reset_link(raw_token)
    try:
        send_reset_email(user.email, reset_link)
    except Exception:
        logger.error(
            "Fallo al enviar email de recuperación",
            extra={"event": "password_reset_email_failed", "user_id": user.id},
            exc_info=True,
        )
        raise

    db.commit()

    logger.info(
        "Email de recuperación enviado",
        extra={"event": "password_reset_requested", "user_id": user.id},
    )

    return generic_response


def confirm_password_reset(
    db: Session,
    token: str,
    new_password: str,
) -> dict:
    

    token_hash = hash_reset_token(token)
    token_record = get_password_reset_token_by_hash(db, token_hash)

    if not token_record:
        logger.warning(
            "Reset de contraseña rechazado: token inexistente",
            extra={"event": "password_reset_invalid_token", "reason": "not_found"},
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El enlace no es válido."
        )

    if token_record.used_at is not None:
        logger.warning(
            "Reset de contraseña rechazado: token ya usado",
            extra={"event": "password_reset_invalid_token", "reason": "already_used", "user_id": token_record.user_id},
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El enlace no es válido."
        )

    if token_record.expires_at < datetime.now(UTC):
        logger.warning(
            "Reset de contraseña rechazado: token expirado",
            extra={"event": "password_reset_invalid_token", "reason": "expired", "user_id": token_record.user_id},
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El enlace no es válido."
        )

    user = get_user_by_id(db, token_record.user_id)

    if not user:
        logger.warning(
            "Reset de contraseña rechazado: usuario no encontrado",
            extra={"event": "password_reset_invalid_token", "reason": "user_not_found"},
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El enlace no es válido."
        )

    user.hashed_password = password_hash.hash(new_password)
    token_record.used_at = datetime.now(UTC)

    other_tokens = get_other_unused_tokens_by_user_id(
        db=db,
        user_id=user.id,
        current_token_id=token_record.id
    )
    invalidate_tokens(other_tokens, datetime.now(UTC))

    revoke_tokens_by_user(db, user.id)

    db.commit()

    logger.info(
        "Contraseña actualizada",
        extra={"event": "password_reset_confirmed", "user_id": user.id},
    )

    return {"message": "La contraseña fue actualizada correctamente."}