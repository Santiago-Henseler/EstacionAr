import html
import json
import secrets
from urllib.parse import urlencode
from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from fastapi.responses import HTMLResponse, RedirectResponse
from app.config import RATE_LIMIT_LOGIN, RATE_LIMIT_FORGOT_PASSWORD, GOOGLE_REDIRECT_URI, RESET_PASSWORD_URL
from sqlalchemy.orm import Session
from app.database import get_db
from app.limiter import limiter
from app.schemas.auth import TokenResponse, LoginRequest, RefreshRequest
from app.schemas.password_reset import ResetPasswordRequest, ForgotPasswordRequest, ForgotPasswordResponse, ResetPasswordResponse
from app.services.auth_service import login_user, refresh_access_token
from app.services.password_reset_service import request_password_reset, confirm_password_reset
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
        path="/",
    )
    return response


@auth_router.get("/google/callback")
def google_callback(
    response: Response,
    code: str,
    state: str,
    google_oauth_state: str | None = Cookie(None),
    db: Session = Depends(get_db),
):
    if google_oauth_state and not secrets.compare_digest(state, google_oauth_state):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid OAuth state")

    response.delete_cookie(GOOGLE_STATE_COOKIE, path="/")
    tokens = login_or_register_google_user(db, code)

    deep_link = (
        "estacionar://oauth-callback?"
        + urlencode({
            "access_token": tokens["access_token"],
            "refresh_token": tokens["refresh_token"],
        })
    )

    meta_deep_link = html.escape(deep_link, quote=True)
    script_deep_link = (
        json.dumps(deep_link)
    	.replace("<", "\\u003c")
    	.replace(">", "\\u003e")
    	.replace("&", "\\u0026")
    )	

    return HTMLResponse(content=f"""
    <html>
        <head>
            <meta http-equiv="refresh" content="0;url={meta_deep_link}">
        </head>
        <body>
            <script>window.location.href = {script_deep_link};</script>
        </body>
    </html>
    """)

@auth_router.get("/reset-password/redirect")
def reset_password_redirect(token: str):
    deep_link = f"{RESET_PASSWORD_URL}?{urlencode({'token': token})}"
    return HTMLResponse(content=f"""
        <html>
            <head><meta http-equiv="refresh" content="0;url={html.escape(deep_link)}"></head>
            <body><script>window.location.href = {html.escape(json.dumps(deep_link), quote=False)};</script></body>
        </html>
    """)


@auth_router.post("/forgot-password", response_model=ForgotPasswordResponse)
@limiter.limit(RATE_LIMIT_FORGOT_PASSWORD)
def forgot_password_endpoint(
    request: Request,
    payload: ForgotPasswordRequest,
    db: Session = Depends(get_db)
):
    return request_password_reset(db, payload.email)


@auth_router.post("/reset-password", response_model=ResetPasswordResponse)
def reset_password_endpoint(
    payload: ResetPasswordRequest,
    db: Session = Depends(get_db)
):
    return confirm_password_reset(
        db=db,
        token=payload.token,
        new_password=payload.new_password,
    )
