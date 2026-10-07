from datetime import datetime, timedelta, UTC
from app.models.refresh_token import RefreshToken
from conftest import TestingSessionLocal

VALID_PASSWORD = "PasswordDeTest1!"
USER_EMAIL = "refresh@test.com"


def create_test_user(client, email=USER_EMAIL):
    client.post("/users", json={"name": "Refresh User", "email": email, "password": VALID_PASSWORD})


def login(client, email=USER_EMAIL) -> dict:
    response = client.post("/auth/login", json={"email": email, "password": VALID_PASSWORD})
    return response.json()


def test_refresh_returns_new_access_and_refresh_token(client):
    create_test_user(client)
    tokens = login(client)
    response = client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body
    assert "refresh_token" in body
    assert body["refresh_token"] != tokens["refresh_token"]


def test_refresh_old_token_is_revoked_after_use(client):
    create_test_user(client)
    tokens = login(client)
    client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    response = client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert response.status_code == 401


def test_refresh_invalid_token(client):
    response = client.post("/auth/refresh", json={"refresh_token": "token_inventado"})
    assert response.status_code == 401


def test_refresh_expired_token(client):
    create_test_user(client)
    tokens = login(client)

    db = TestingSessionLocal()
    try:
        record = db.query(RefreshToken).first()
        record.expires_at = datetime.now(UTC) - timedelta(days=1)
        db.commit()
    finally:
        db.close()

    response = client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert response.status_code == 401


def test_refresh_revoked_token(client):
    create_test_user(client)
    tokens = login(client)

    db = TestingSessionLocal()
    try:
        record = db.query(RefreshToken).first()
        record.revoked_at = datetime.now(UTC)
        db.commit()
    finally:
        db.close()

    response = client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert response.status_code == 401


def test_login_cleans_expired_tokens(client):
    create_test_user(client)
    login(client)

    db = TestingSessionLocal()
    try:
        record = db.query(RefreshToken).first()
        record.expires_at = datetime.now(UTC) - timedelta(days=1)
        db.commit()
    finally:
        db.close()

    login(client)

    db = TestingSessionLocal()
    try:
        count = db.query(RefreshToken).count()
        assert count == 1
    finally:
        db.close()
