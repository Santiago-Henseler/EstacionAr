def create_test_user(client):
    payload = {
        "name": "Rodrigo",
        "email": "rodrigo@test.com",
        "password": "PasswordDeTest1!"
    }
    return client.post("/users", json=payload)


def test_login_success(client):
    create_test_user(client)

    payload = {
        "email": "rodrigo@test.com",
        "password": "PasswordDeTest1!"
    }

    response = client.post("/auth/login", json=payload)

    assert response.status_code == 200

    body = response.json()

    assert "access_token" in body
    assert "refresh_token" in body
    assert "token_type" in body
    assert isinstance(body["access_token"], str)
    assert isinstance(body["refresh_token"], str)
    assert len(body["access_token"]) > 0
    assert len(body["refresh_token"]) > 0
    assert body["token_type"] == "bearer"


def test_login_wrong_password(client):
    create_test_user(client)

    payload = {
        "email": "rodrigo@test.com",
        "password": "PasswordIncorrecta1!"
    }

    response = client.post("/auth/login", json=payload)

    assert response.status_code == 401

    body = response.json()
    assert body["detail"] == "Invalid Credentials"


def test_login_nonexistent_email(client):
    payload = {
        "email": "noexiste@test.com",
        "password": "PasswordDeTest1!"
    }

    response = client.post("/auth/login", json=payload)

    assert response.status_code == 401

    body = response.json()
    assert body["detail"] == "Invalid Credentials"


def test_login_invalid_email_format(client):
    payload = {
        "email": "esto-no-es-un-mail",
        "password": "PasswordDeTest1!"
    }

    response = client.post("/auth/login", json=payload)

    assert response.status_code == 422


def test_login_email_as_int(client):
    payload = {
        "email": 12345,
        "password": "PasswordDeTest1!"
    }

    response = client.post("/auth/login", json=payload)

    assert response.status_code == 422


def test_login_email_as_boolean(client):
    payload = {
        "email": True,
        "password": "PasswordDeTest1!"
    }

    response = client.post("/auth/login", json=payload)

    assert response.status_code == 422


def test_login_password_as_int(client):
    payload = {
        "email": "rodrigo@test.com",
        "password": 12345
    }

    response = client.post("/auth/login", json=payload)

    assert response.status_code == 422


def test_login_password_as_boolean(client):
    payload = {
        "email": "rodrigo@test.com",
        "password": False
    }

    response = client.post("/auth/login", json=payload)

    assert response.status_code == 422


def test_login_empty_email(client):
    payload = {
        "email": "",
        "password": "PasswordDeTest1!"
    }

    response = client.post("/auth/login", json=payload)

    assert response.status_code == 422


def test_login_empty_password(client):
    payload = {
        "email": "rodrigo@test.com",
        "password": ""
    }

    response = client.post("/auth/login", json=payload)

    assert response.status_code == 422


def test_login_missing_email(client):
    payload = {
        "password": "PasswordDeTest1!"
    }

    response = client.post("/auth/login", json=payload)

    assert response.status_code == 422


def test_login_missing_password(client):
    payload = {
        "email": "rodrigo@test.com"
    }

    response = client.post("/auth/login", json=payload)

    assert response.status_code == 422


def test_login_empty_body(client):
    response = client.post("/auth/login", json={})

    assert response.status_code == 422


def test_login_null_email(client):
    payload = {
        "email": None,
        "password": "PasswordDeTest1!"
    }

    response = client.post("/auth/login", json=payload)

    assert response.status_code == 422


def test_login_null_password(client):
    payload = {
        "email": "rodrigo@test.com",
        "password": None
    }

    response = client.post("/auth/login", json=payload)

    assert response.status_code == 422


def test_login_google_only_user(client, db):
    from app.models.user import User
    db.add(User(name="Google User", email="google@test.com", google_id="google-id-1", hashed_password=None))
    db.commit()

    response = client.post("/auth/login", json={"email": "google@test.com", "password": "PasswordDeTest1!"})

    assert response.status_code == 401


def test_login_email_is_case_insensitive(client):
    create_test_user(client)

    response = client.post("/auth/login", json={"email": "RODRIGO@test.com", "password": "PasswordDeTest1!"})

    assert response.status_code == 200
