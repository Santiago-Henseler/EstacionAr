import html
import re
from unittest.mock import MagicMock, patch
from urllib.parse import parse_qs, urlparse
from app.models.user import User


GOOGLE_USER_INFO = {
    "sub": "google-id-123",
    "email": "rodrigo@test.com",
    "name": "Rodrigo Test",
    "email_verified": True,
}


def _start_google_login(client) -> str:
    response = client.get("/auth/google", follow_redirects=False)
    return parse_qs(urlparse(response.headers["location"]).query)["state"][0]


def _callback(client, code="valid-code"):
    state = _start_google_login(client)
    return client.get(f"/auth/google/callback?code={code}&state={state}")


def _deep_link_tokens(response) -> dict:
    """Extrae los tokens del deep link estacionar://oauth-callback que devuelve el HTML del callback."""
    match = re.search(r'url=(estacionar://oauth-callback\?[^"]+)"', response.text)
    assert match, "El callback no devolvió el deep link esperado"
    query = urlparse(html.unescape(match.group(1))).query
    return {k: v[0] for k, v in parse_qs(query).items()}


def _mock_httpx_client(token_status=200, userinfo_status=200, user_info=None):
    if user_info is None:
        user_info = GOOGLE_USER_INFO

    token_response = MagicMock()
    token_response.status_code = token_status
    token_response.json.return_value = {"access_token": "google-access-token"}

    userinfo_response = MagicMock()
    userinfo_response.status_code = userinfo_status
    userinfo_response.json.return_value = user_info

    mock_client = MagicMock()
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)
    mock_client.post.return_value = token_response
    mock_client.get.return_value = userinfo_response

    return mock_client


def test_google_login_redirects_to_google(client):
    response = client.get("/auth/google", follow_redirects=False)

    assert response.status_code == 307
    location = response.headers["location"]
    assert location.startswith("https://accounts.google.com/")
    params = parse_qs(urlparse(location).query)
    assert "openid" in params["scope"][0]
    assert params["state"][0] == response.cookies["google_oauth_state"]


def test_google_callback_new_user(client):
    mock_client = _mock_httpx_client()

    with patch("httpx.Client", return_value=mock_client):
        response = _callback(client)

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    tokens = _deep_link_tokens(response)
    assert tokens["access_token"]
    assert tokens["refresh_token"]


def test_google_callback_existing_user_without_google_id(client):
    client.post("/users", json={
        "name": "Rodrigo Test",
        "email": "rodrigo@test.com",
        "password": "PasswordDeTest1!"
    })

    mock_client = _mock_httpx_client()

    with patch("httpx.Client", return_value=mock_client):
        response = _callback(client)

    assert response.status_code == 200
    assert "access_token" in _deep_link_tokens(response)


def test_google_callback_existing_user_with_google_id(client):
    mock_client = _mock_httpx_client()

    with patch("httpx.Client", return_value=mock_client):
        _callback(client)
        response = _callback(client)

    assert response.status_code == 200
    assert "access_token" in _deep_link_tokens(response)


def test_google_callback_token_exchange_fails(client):
    mock_client = _mock_httpx_client(token_status=400)

    with patch("httpx.Client", return_value=mock_client):
        response = _callback(client, "invalid-code")

    assert response.status_code == 503


def test_google_callback_userinfo_fails(client):
    mock_client = _mock_httpx_client(userinfo_status=401)

    with patch("httpx.Client", return_value=mock_client):
        response = _callback(client)

    assert response.status_code == 503


def test_google_callback_network_error_on_token(client):
    import httpx

    mock_client = MagicMock()
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)
    mock_client.post.side_effect = httpx.RequestError("connection error")

    with patch("httpx.Client", return_value=mock_client):
        response = _callback(client)

    assert response.status_code == 503


def test_google_callback_network_error_on_userinfo(client):
    import httpx

    token_response = MagicMock()
    token_response.status_code = 200
    token_response.json.return_value = {"access_token": "google-access-token"}

    call_count = 0

    def client_factory(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        mock = MagicMock()
        mock.__enter__ = MagicMock(return_value=mock)
        mock.__exit__ = MagicMock(return_value=False)
        if call_count == 1:
            mock.post.return_value = token_response
        else:
            mock.get.side_effect = httpx.RequestError("connection error")
        return mock

    with patch("httpx.Client", side_effect=client_factory):
        response = _callback(client)

    assert response.status_code == 503


def test_google_callback_missing_code(client):
    state = _start_google_login(client)
    response = client.get(f"/auth/google/callback?state={state}")

    assert response.status_code == 422


def test_google_callback_missing_state(client):
    response = client.get("/auth/google/callback?code=valid-code")

    assert response.status_code == 422


def test_google_callback_state_mismatch(client):
    _start_google_login(client)

    with patch("httpx.Client") as mock_httpx:
        response = client.get("/auth/google/callback?code=valid-code&state=otro-state")

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid OAuth state"
    mock_httpx.assert_not_called()


def test_google_callback_without_state_cookie_is_accepted(client):
    # Comportamiento elegido (baa91f5): si la cookie de state no llega (p. ej. desde la app),
    # no se valida el state. Solo se rechaza cuando la cookie existe y no coincide.
    mock_client = _mock_httpx_client()

    with patch("httpx.Client", return_value=mock_client):
        response = client.get("/auth/google/callback?code=valid-code&state=cualquiera")

    assert response.status_code == 200
    assert "access_token" in _deep_link_tokens(response)


def test_google_callback_deletes_state_cookie(client):
    state = _start_google_login(client)
    mock_client = _mock_httpx_client()

    with patch("httpx.Client", return_value=mock_client):
        response = client.get(f"/auth/google/callback?code=valid-code&state={state}")

    assert response.status_code == 200
    set_cookie = response.headers.get("set-cookie", "")
    assert "google_oauth_state=" in set_cookie
    assert "Max-Age=0" in set_cookie
    assert "google_oauth_state" not in client.cookies


def test_google_callback_unverified_email_does_not_link_account(client, db):
    client.post("/users", json={
        "name": "Rodrigo Test",
        "email": "rodrigo@test.com",
        "password": "PasswordDeTest1!"
    })
    mock_client = _mock_httpx_client(user_info={**GOOGLE_USER_INFO, "email_verified": False})

    with patch("httpx.Client", return_value=mock_client):
        response = _callback(client)

    assert response.status_code == 400
    user = db.query(User).filter(User.email == "rodrigo@test.com").first()
    assert user.google_id is None
