from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import get_db

health_router = APIRouter(tags=["health"])


@health_router.get("/livez", status_code=200)
def liveness():
    return {"status": "alive"}


@health_router.get("/readyz", status_code=200)
def readiness(response: Response, db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        response.status_code = 503
        return {"status": "unavailable", "detail": "database unreachable"}
    return {"status": "ready"}
