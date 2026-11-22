from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, field_validator


class ExperienceRatingCreate(BaseModel):
    stars: int = Field(..., ge=1, le=5)
    comment: str | None = Field(None, max_length=500)

    @field_validator("comment")
    @classmethod
    def blank_comment_to_none(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None


class ExperienceRatingResponse(BaseModel):
    id: int
    stars: int
    comment: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ExperienceRatingEligibility(BaseModel):
    eligible: bool
    next_eligible_at: datetime | None = None
