from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.experience_rating import (
    ExperienceRatingCreate,
    ExperienceRatingEligibility,
    ExperienceRatingResponse,
)
from app.services.experience_rating_service import (
    dismiss_experience_rating,
    get_eligibility,
    rate_experience,
)


experience_rating_router = APIRouter(prefix="/experience-ratings", tags=["Experience ratings"])


@experience_rating_router.get("/eligibility", response_model=ExperienceRatingEligibility)
def eligibility(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return get_eligibility(db, current_user)


@experience_rating_router.post("", response_model=ExperienceRatingResponse, status_code=status.HTTP_201_CREATED)
def rate(data: ExperienceRatingCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return rate_experience(db, current_user, data)


@experience_rating_router.post("/dismiss", status_code=status.HTTP_204_NO_CONTENT)
def dismiss(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    dismiss_experience_rating(db, current_user)
