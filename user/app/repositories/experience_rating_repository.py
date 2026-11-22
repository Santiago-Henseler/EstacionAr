from sqlalchemy.orm import Session
from app.models.experience_rating import ExperienceRating


def get_last_rating_by_user(db: Session, user_id: int) -> ExperienceRating | None:
    return (
        db.query(ExperienceRating)
        .filter(ExperienceRating.user_id == user_id)
        .order_by(ExperienceRating.created_at.desc())
        .first()
    )


def save_rating(db: Session, rating: ExperienceRating) -> ExperienceRating:
    db.add(rating)
    db.commit()
    db.refresh(rating)
    return rating
