from urllib.parse import urlencode
from datetime import timedelta

import httpx
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.config import (
    GOOGLE_CLIENT_ID,
    GOOGLE_CLIENT_SECRET,
    GOOGLE_REDIRECT_URI,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)
from app.models.user import User
from app.repositories.user_repository import (
    get_user_by_email,
    get_user_by_google_id,
    save_user,
)
from app.services.auth_service import create_access_token, _generate_refresh_token

_GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
_GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"  # nosec B105
_GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"


def get_google_auth_url(state: str) -> str:
    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
    }
    return f"{_GOOGLE_AUTH_URL}?{urlencode(params)}"


def _fetch_google_user_info(code: str) -> dict:
    try:
        with httpx.Client(timeout=10) as client:
            token_resp = client.post(_GOOGLE_TOKEN_URL, data={
                "code": code,
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "redirect_uri": GOOGLE_REDIRECT_URI,
                "grant_type": "authorization_code",
            })
    except httpx.RequestError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google authentication service is unavailable. Please log in with email and password.",
        )

    if token_resp.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google authentication service is unavailable. Please log in with email and password.",
        )

    access_token = token_resp.json().get("access_token")

    try:
        with httpx.Client(timeout=10) as client:
            userinfo_resp = client.get(
                _GOOGLE_USERINFO_URL,
                headers={"Authorization": f"Bearer {access_token}"},
            )
    except httpx.RequestError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google authentication service is unavailable. Please log in with email and password.",
        )

    if userinfo_resp.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google authentication service is unavailable. Please log in with email and password.",
        )

    return userinfo_resp.json()


def login_or_register_google_user(db: Session, code: str) -> dict:
    user_info = _fetch_google_user_info(code)

    if not user_info.get("email_verified"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google account email is not verified.",
        )

    google_id = user_info["sub"]
    email = user_info["email"].lower()
    name = user_info.get("name", "")

    user = get_user_by_google_id(db, google_id)

    if not user:
        user = get_user_by_email(db, email)
        if user:
            user.google_id = google_id
            db.commit()
            db.refresh(user)
        else:
            user = User(name=name, email=email, google_id=google_id, hashed_password=None)
            save_user(db, user)

    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )

    refresh_token = _generate_refresh_token(db, user.id)
    db.commit()
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}  # nosec B105
