from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field

ReportReason = Literal["no_habia_lugar", "zona_prohibida", "zona_inaccesible", "otro"]


class ReportCreate(BaseModel):
    street_name: str = Field(..., min_length=1)
    level: int = Field(..., ge=0)
    reason: ReportReason
    description: str | None = Field(None, max_length=280)


class ReportResponse(BaseModel):
    id: int
    type: str
    reason: str
    street_name: str
    level: int
    a_init: int
    hour: int
    description: str | None = None
    status: str
    created_at: datetime
