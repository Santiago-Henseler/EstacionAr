


def test_create_user(client):
    payload = {
        "name": "Rodrigo",
        "email": "rodrigo@test.com",
        "password": "PasswordDeTest1!"
    }

    response = client.post("/users", json=payload)

    assert response.status_code == 201

    body = response.json()

    assert body["name"] == "Rodrigo"
    assert body["email"] == "rodrigo@test.com"
    assert "id" in body


def test_create_user_without_uppercase(client):
    payload = {
        "name": "Rodrigo",
        "email": "rodrigo@test.com",
        "password": "passworddetest1!"
    }

    response = client.post("/users", json=payload)

    assert response.status_code == 422

    body = response.json()

    assert "detail" in body
    assert any(
        error["loc"][-1] == "password"
        for error in body["detail"]
    )

def test_create_user_without_lowercase(client):
    payload = {
        "name": "Rodrigo",
        "email": "rodrigo@test.com",
        "password": "PASSWORDDETEST1!"
    }

    response = client.post("/users", json=payload)

    assert response.status_code == 422

    body = response.json()

    assert "detail" in body
    assert any(
        error["loc"][-1] == "password"
        for error in body["detail"]
    )

def test_create_user_without_numbers(client):
    payload = {
        "name": "Rodrigo",
        "email": "rodrigo@test.com",
        "password": "PasswordDeTest!"
    }

    response = client.post("/users", json=payload)

    assert response.status_code == 422

    body = response.json()

    assert "detail" in body
    assert any(
        error["loc"][-1] == "password"
        for error in body["detail"]
    )

def test_create_user_without_special_character(client):
    payload = {
        "name": "Rodrigo",
        "email": "rodrigo@test.com",
        "password": "PasswordDeTest1"
    }

    response = client.post("/users", json=payload)

    assert response.status_code == 422

    body = response.json()

    assert "detail" in body
    assert any(
        error["loc"][-1] == "password"
        for error in body["detail"]
    )

def test_create_user_with_less_than_8_characters(client):
    payload = {
        "name": "Rodrigo",
        "email": "rodrigo@test.com",
        "password": "Pass"
    }

    response = client.post("/users", json=payload)

    assert response.status_code == 422

    body = response.json()

    assert "detail" in body
    assert any(
        error["loc"][-1] == "password"
        for error in body["detail"]
    )

def test_create_user_with_number_as_name(client):
    payload = {
        "name": 1,
        "email": "rodrigo@test.com",
        "password": "Pass"
    }

    response = client.post("/users", json=payload)

    assert response.status_code == 422

    body = response.json()

    assert "detail" in body
    assert any(
        error["loc"][-1] == "name"
        for error in body["detail"]
    )

def test_create_user_with_boolean_as_name(client):
    payload = {
        "name": True,
        "email": "rodrigo@test.com",
        "password": "Pass"
    }

    response = client.post("/users", json=payload)

    assert response.status_code == 422

    body = response.json()

    assert "detail" in body
    assert any(
        error["loc"][-1] == "name"
        for error in body["detail"]
    )

def test_create_user_with_list_as_name(client):
    payload = {
        "name": [True,False],
        "email": "rodrigo@test.com",
        "password": "Pass"
    }

    response = client.post("/users", json=payload)

    assert response.status_code == 422

    body = response.json()

    assert "detail" in body
    assert any(
        error["loc"][-1] == "name"
        for error in body["detail"]
    )

def test_create_user_with_incorrect_email(client):
    payload = {
        "name": "Rodrigo",
        "email": "rodrigo@",
        "password": "Pass"
    }

    response = client.post("/users", json=payload)

    assert response.status_code == 422

    body = response.json()

    assert "detail" in body
    assert any(
        error["loc"][-1] == "email"
        for error in body["detail"]
    )

def test_create_user_with_mail_as_boolean(client):
    payload = {
        "name": "Rodrigo",
        "email": True,
        "password": "Pass"
    }

    response = client.post("/users", json=payload)

    assert response.status_code == 422

    body = response.json()

    assert "detail" in body
    assert any(
        error["loc"][-1] == "email"
        for error in body["detail"]
    )

def test_create_user_with_mail_as_integer(client):
    payload = {
        "name": "Rodrigo",
        "email": 1,
        "password": "Pass"
    }

    response = client.post("/users", json=payload)

    assert response.status_code == 422

    body = response.json()

    assert "detail" in body
    assert any(
        error["loc"][-1] == "email"
        for error in body["detail"]
    )

def test_create_user_with_mail_as_list(client):
    payload = {
        "name": "Rodrigo",
        "email": [False,True],
        "password": "Pass"
    }

    response = client.post("/users", json=payload)

    assert response.status_code == 422

    body = response.json()

    assert "detail" in body
    assert any(
        error["loc"][-1] == "email"
        for error in body["detail"]
    )


def test_create_user_email_is_case_insensitive(client):
    payload = {"name": "Rodrigo", "email": "Rodrigo@Test.com", "password": "PasswordDeTest1!"}

    response = client.post("/users", json=payload)
    assert response.status_code == 201
    assert response.json()["email"] == "rodrigo@test.com"

    duplicate = client.post("/users", json={**payload, "email": "rodrigo@test.com"})
    assert duplicate.status_code == 400
