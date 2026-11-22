from datetime import datetime, timedelta, UTC
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.models.experience_rating import ExperienceRating
from app.models.user import User
from app.repositories.experience_rating_repository import get_last_rating_by_user, save_rating
from app.schemas.experience_rating import ExperienceRatingCreate, ExperienceRatingEligibility

# El pedido de puntaje aparece como máximo una vez cada 30 días, se haya respondido o descartado
COOLDOWN = timedelta(days=30)


def _next_eligible_at(db: Session, user: User) -> datetime | None:
    last = get_last_rating_by_user(db, user.id)
    if last is None:
        return None
    created_at = last.created_at
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=UTC)
    next_at = created_at + COOLDOWN
    return next_at if next_at > datetime.now(UTC) else None


def get_eligibility(db: Session, user: User) -> ExperienceRatingEligibility:
    next_at = _next_eligible_at(db, user)
    return ExperienceRatingEligibility(eligible=next_at is None, next_eligible_at=next_at)


def _ensure_eligible(db: Session, user: User) -> None:
    next_at = _next_eligible_at(db, user)
    if next_at is not None:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"experience rating already requested, try again after {next_at.isoformat()}",
        )


def rate_experience(db: Session, user: User, data: ExperienceRatingCreate) -> ExperienceRating:
    _ensure_eligible(db, user)
    return save_rating(db, ExperienceRating(user_id=user.id, stars=data.stars, comment=data.comment))


def dismiss_experience_rating(db: Session, user: User) -> None:
    _ensure_eligible(db, user)
    save_rating(db, ExperienceRating(user_id=user.id))
