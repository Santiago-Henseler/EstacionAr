from datetime import datetime, timedelta, UTC
from unittest.mock import patch, MagicMock

import pytest

from app.models.password_reset_token import PasswordResetToken
from app.services.password_reset_service import send_reset_email
from conftest import TestingSessionLocal

VALID_PASSWORD = "PasswordDeTest1!"
USER_EMAIL = "user@test.com"


def create_test_user(client, email=USER_EMAIL):
    client.post("/users", json={"name": "Test User", "email": email, "password": VALID_PASSWORD})


def get_reset_token(client, email=USER_EMAIL) -> str:
    with patch("app.services.password_reset_service.send_reset_email") as mock_send:
        client.post("/auth/forgot-password", json={"email": email})
    reset_link = mock_send.call_args[0][1]
    return reset_link.split("token=")[1]




def test_send_reset_email_calls_sendgrid():
    with patch("app.services.password_reset_service.SendGridAPIClient") as mock_client:
        send_reset_email("dest@test.com", "http://example.com/reset?token=abc")
        mock_client.return_value.send.assert_called_once()




def test_forgot_password_unregistered_email(client):
    response = client.post("/auth/forgot-password", json={"email": "noexiste@test.com"})
    assert response.status_code == 200
    assert "enlace" in response.json()["message"]


def test_forgot_password_success(client):
    create_test_user(client)
    with patch("app.services.password_reset_service.send_reset_email") as mock_send:
        response = client.post("/auth/forgot-password", json={"email": USER_EMAIL})
    assert response.status_code == 200
    assert "enlace" in response.json()["message"]
    mock_send.assert_called_once()


def test_forgot_password_invalidates_previous_active_token(client):
    create_test_user(client)
    first_token = get_reset_token(client)

    with patch("app.services.password_reset_service.send_reset_email"):
        client.post("/auth/forgot-password", json={"email": USER_EMAIL})

    response = client.post("/auth/reset-password", json={
        "token": first_token,
        "new_password": VALID_PASSWORD,
        "confirm_password": VALID_PASSWORD,
    })
    assert response.status_code == 400


def test_forgot_password_rate_limit(client):
    create_test_user(client)
    for _ in range(3):
        with patch("app.services.password_reset_service.send_reset_email"):
            client.post("/auth/forgot-password", json={"email": USER_EMAIL})

    with patch("app.services.password_reset_service.send_reset_email") as mock_send:
        response = client.post("/auth/forgot-password", json={"email": USER_EMAIL})

    assert response.status_code == 200
    mock_send.assert_not_called()




def test_reset_password_success(client):
    create_test_user(client)
    token = get_reset_token(client)
    response = client.post("/auth/reset-password", json={
        "token": token,
        "new_password": VALID_PASSWORD,
        "confirm_password": VALID_PASSWORD,
    })
    assert response.status_code == 200
    assert response.json()["message"] == "La contraseña fue actualizada correctamente."


def test_reset_password_invalid_token(client):
    response = client.post("/auth/reset-password", json={
        "token": "tokeninvalido",
        "new_password": VALID_PASSWORD,
        "confirm_password": VALID_PASSWORD,
    })
    assert response.status_code == 400
    assert response.json()["detail"] == "El enlace no es válido."


def test_reset_password_already_used_token(client):
    create_test_user(client)
    token = get_reset_token(client)
    client.post("/auth/reset-password", json={
        "token": token,
        "new_password": VALID_PASSWORD,
        "confirm_password": VALID_PASSWORD,
    })
    response = client.post("/auth/reset-password", json={
        "token": token,
        "new_password": VALID_PASSWORD,
        "confirm_password": VALID_PASSWORD,
    })
    assert response.status_code == 400
    assert response.json()["detail"] == "El enlace no es válido."


def test_reset_password_expired_token(client):
    create_test_user(client)
    token = get_reset_token(client)

    db = TestingSessionLocal()
    try:
        record = db.query(PasswordResetToken).first()
        record.expires_at = datetime.now(UTC) - timedelta(hours=2)
        db.commit()
    finally:
        db.close()

    response = client.post("/auth/reset-password", json={
        "token": token,
        "new_password": VALID_PASSWORD,
        "confirm_password": VALID_PASSWORD,
    })
    assert response.status_code == 400
    assert response.json()["detail"] == "El enlace no es válido."


def test_reset_password_user_not_found(client):
    create_test_user(client)
    token = get_reset_token(client)

    with patch("app.services.password_reset_service.get_user_by_id", return_value=None):
        response = client.post("/auth/reset-password", json={
            "token": token,
            "new_password": VALID_PASSWORD,
            "confirm_password": VALID_PASSWORD,
        })

    assert response.status_code == 400
    assert response.json()["detail"] == "El enlace no es válido."


def test_redirect_returns_response_with_any_token(client):
    response = client.get("/auth/reset-password/redirect?token=cualquier_string_inventado")
    assert response.status_code == 200
    assert len(response.content) > 0


def test_redirect_escapes_token(client):
    response = client.get("/auth/reset-password/redirect", params={"token": '"></script><script>alert(1)</script>'})
    assert response.status_code == 200
    assert "<script>alert(1)</script>" not in response.text


def test_reset_password_invalidates_other_unused_tokens(client):
    create_test_user(client)
    token1 = get_reset_token(client)

    db = TestingSessionLocal()
    try:
        record = db.query(PasswordResetToken).order_by(PasswordResetToken.id).first()
        record.expires_at = datetime.now(UTC) - timedelta(hours=2)
        db.commit()
    finally:
        db.close()

    token2 = get_reset_token(client)

    client.post("/auth/reset-password", json={
        "token": token2,
        "new_password": VALID_PASSWORD,
        "confirm_password": VALID_PASSWORD,
    })

    db = TestingSessionLocal()
    try:
        record = db.query(PasswordResetToken).order_by(PasswordResetToken.id).first()
        assert record.used_at is not None
    finally:
        db.close()


def test_reset_password_revokes_refresh_tokens(client):
    create_test_user(client)
    tokens = client.post("/auth/login", json={"email": USER_EMAIL, "password": VALID_PASSWORD}).json()
    token = get_reset_token(client)

    client.post("/auth/reset-password", json={
        "token": token,
        "new_password": "OtraPassword1!",
        "confirm_password": "OtraPassword1!",
    })

    response = client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert response.status_code == 401


def test_login_with_new_password_after_reset(client):
    create_test_user(client)
    token = get_reset_token(client)

    client.post("/auth/reset-password", json={
        "token": token,
        "new_password": "OtraPassword1!",
        "confirm_password": "OtraPassword1!",
    })

    old = client.post("/auth/login", json={"email": USER_EMAIL, "password": VALID_PASSWORD})
    new = client.post("/auth/login", json={"email": USER_EMAIL, "password": "OtraPassword1!"})
    assert old.status_code == 401
    assert new.status_code == 200
