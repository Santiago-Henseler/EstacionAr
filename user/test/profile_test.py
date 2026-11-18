from unittest.mock import patch
from app.services.auth_service import create_access_token


def test_get_own_profile_success(client, regular_user, auth_headers):
    response = client.get("/users/me", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == regular_user.id
    assert body["email"] == regular_user.email
    assert body["name"] == regular_user.name


def test_get_own_profile_with_login_token(client):
    client.post("/users", json={"name": "Rodrigo", "email": "rodrigo@test.com", "password": "PasswordDeTest1!"})
    tokens = client.post("/auth/login", json={"email": "rodrigo@test.com", "password": "PasswordDeTest1!"}).json()

    response = client.get("/users/me", headers={"Authorization": f"Bearer {tokens['access_token']}"})

    assert response.status_code == 200
    assert response.json()["email"] == "rodrigo@test.com"


def test_get_own_profile_without_token(client):
    response = client.get("/users/me")
    assert response.status_code in (401, 403)


def test_get_own_profile_invalid_token(client):
    response = client.get("/users/me", headers={"Authorization": "Bearer token-invalido"})
    assert response.status_code == 401


def test_get_own_profile_nonexistent_user(client):
    token = create_access_token({"sub": "9999", "email": "nadie@test.com"})
    response = client.get("/users/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401


def test_update_profile_name(client, auth_headers):
    response = client.patch("/users/me", json={"name": "Nuevo Nombre"}, headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["name"] == "Nuevo Nombre"


def test_update_profile_without_token(client):
    response = client.patch("/users/me", json={"name": "Nuevo Nombre"})
    assert response.status_code in (401, 403)


def test_update_profile_name_too_short(client, auth_headers):
    response = client.patch("/users/me", json={"name": "ab"}, headers=auth_headers)
    assert response.status_code == 422


def test_delete_own_profile_success(client, auth_headers):
    response = client.delete("/users/me", headers=auth_headers)
    assert response.status_code == 204

    # Verify user is deleted and cannot access /users/me anymore
    response = client.get("/users/me", headers=auth_headers)
    assert response.status_code == 401


def test_delete_own_profile_without_token(client):
    response = client.delete("/users/me")
    assert response.status_code in (401, 403)


def test_delete_profile_with_refresh_and_reset_tokens(client, regular_user):
    # El login crea un refresh token asociado al usuario
    login = client.post("/auth/login", json={"email": regular_user.email, "password": "UserPass1!"})
    assert login.status_code == 200
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    # El pedido de reset crea un password reset token asociado al usuario
    with patch("app.services.password_reset_service.send_reset_email"):
        client.post("/auth/forgot-password", json={"email": regular_user.email})

    response = client.delete("/users/me", headers=headers)
    assert response.status_code == 204

    # El refresh token del usuario borrado ya no sirve
    refresh = client.post("/auth/refresh", json={"refresh_token": login.json()["refresh_token"]})
    assert refresh.status_code == 401
