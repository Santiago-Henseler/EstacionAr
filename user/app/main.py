import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.limiter import limiter
from app.routers.user_router import user_router
from app.routers.auth_router import auth_router
from app.routers.health_router import health_router
from app.routers.experience_rating_router import experience_rating_router
from app.database import engine, Base
from app.models.user import User
from app.models.refresh_token import RefreshToken
from app.models.password_reset_token import PasswordResetToken
from app.models.experience_rating import ExperienceRating


Base.metadata.create_all(bind=engine)

os.makedirs("uploads/profile_pictures", exist_ok=True)

app = FastAPI(title="Users API")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.mount("/static", StaticFiles(directory="uploads"), name="static")

app.include_router(user_router)
app.include_router(auth_router)
app.include_router(health_router)
app.include_router(experience_rating_router)
