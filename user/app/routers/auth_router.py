import secrets
from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from app.config import RATE_LIMIT_LOGIN, GOOGLE_REDIRECT_URI
from sqlalchemy.orm import Session
from app.database import get_db
from app.limiter import limiter
from app.schemas.auth import TokenResponse, LoginRequest, RefreshRequest
from app.services.auth_service import login_user, refresh_access_token
from app.services.google_auth_service import get_google_auth_url, login_or_register_google_user


auth_router = APIRouter(prefix="/auth", tags=["Auth"])

GOOGLE_STATE_COOKIE = "google_oauth_state"
GOOGLE_STATE_MAX_AGE_SECONDS = 600


@auth_router.post("/login", response_model=TokenResponse)
@limiter.limit(RATE_LIMIT_LOGIN)
def login_user_endpoint(request: Request, login_data: LoginRequest, db: Session = Depends(get_db)):
    return login_user(login_data, db)


@auth_router.post("/refresh", response_model=TokenResponse)
def refresh_token_endpoint(payload: RefreshRequest, db: Session = Depends(get_db)):
    return refresh_access_token(db, payload.refresh_token)


@auth_router.get("/google")
def google_login():
    state = secrets.token_urlsafe(32)
    response = RedirectResponse(url=get_google_auth_url(state))
    response.set_cookie(
        GOOGLE_STATE_COOKIE,
        state,
        max_age=GOOGLE_STATE_MAX_AGE_SECONDS,
        httponly=True,
        samesite="lax",
        secure=GOOGLE_REDIRECT_URI.startswith("https://"),
    )
    return response


@auth_router.get("/google/callback", response_model=TokenResponse)
def google_callback(
    response: Response,
    code: str,
    state: str,
    google_oauth_state: str | None = Cookie(None),
    db: Session = Depends(get_db),
):
    if not google_oauth_state or not secrets.compare_digest(state, google_oauth_state):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid OAuth state")

    response.delete_cookie(GOOGLE_STATE_COOKIE)
    return login_or_register_google_user(db, code)
