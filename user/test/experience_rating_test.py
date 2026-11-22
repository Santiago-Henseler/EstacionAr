from datetime import datetime, timedelta, UTC
from app.models.experience_rating import ExperienceRating


def _age_last_rating(db, user_id, days):
    rating = db.query(ExperienceRating).filter(ExperienceRating.user_id == user_id).first()
    rating.created_at = datetime.now(UTC) - timedelta(days=days)
    db.commit()


def test_eligible_when_never_rated(client, auth_headers):
    response = client.get("/experience-ratings/eligibility", headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == {"eligible": True, "next_eligible_at": None}


def test_rate_experience_success(client, auth_headers):
    response = client.post("/experience-ratings", json={"stars": 4, "comment": "Muy útil"}, headers=auth_headers)
    assert response.status_code == 201
    body = response.json()
    assert body["stars"] == 4
    assert body["comment"] == "Muy útil"


def test_rate_experience_without_comment(client, auth_headers):
    response = client.post("/experience-ratings", json={"stars": 5}, headers=auth_headers)
    assert response.status_code == 201
    assert response.json()["comment"] is None


def test_blank_comment_is_stored_as_none(client, auth_headers):
    response = client.post("/experience-ratings", json={"stars": 3, "comment": "   "}, headers=auth_headers)
    assert response.status_code == 201
    assert response.json()["comment"] is None


def test_stars_out_of_range(client, auth_headers):
    for stars in (0, 6):
        response = client.post("/experience-ratings", json={"stars": stars}, headers=auth_headers)
        assert response.status_code == 422


def test_comment_too_long(client, auth_headers):
    response = client.post("/experience-ratings", json={"stars": 3, "comment": "a" * 501}, headers=auth_headers)
    assert response.status_code == 422


def test_comment_max_length_ok(client, auth_headers):
    response = client.post("/experience-ratings", json={"stars": 3, "comment": "a" * 500}, headers=auth_headers)
    assert response.status_code == 201


def test_requires_auth(client):
    assert client.get("/experience-ratings/eligibility").status_code in (401, 403)
    assert client.post("/experience-ratings", json={"stars": 4}).status_code in (401, 403)
    assert client.post("/experience-ratings/dismiss").status_code in (401, 403)


def test_not_eligible_after_rating(client, auth_headers):
    client.post("/experience-ratings", json={"stars": 4}, headers=auth_headers)

    response = client.get("/experience-ratings/eligibility", headers=auth_headers)
    body = response.json()
    assert body["eligible"] is False
    assert body["next_eligible_at"] is not None


def test_cannot_rate_twice_within_30_days(client, auth_headers):
    client.post("/experience-ratings", json={"stars": 4}, headers=auth_headers)
    response = client.post("/experience-ratings", json={"stars": 2}, headers=auth_headers)
    assert response.status_code == 429


def test_dismiss_starts_cooldown(client, auth_headers):
    response = client.post("/experience-ratings/dismiss", headers=auth_headers)
    assert response.status_code == 204

    assert client.get("/experience-ratings/eligibility", headers=auth_headers).json()["eligible"] is False
    assert client.post("/experience-ratings", json={"stars": 4}, headers=auth_headers).status_code == 429
    assert client.post("/experience-ratings/dismiss", headers=auth_headers).status_code == 429


def test_eligible_again_after_30_days(client, db, regular_user, auth_headers):
    client.post("/experience-ratings", json={"stars": 4}, headers=auth_headers)
    _age_last_rating(db, regular_user.id, days=31)

    assert client.get("/experience-ratings/eligibility", headers=auth_headers).json()["eligible"] is True
    assert client.post("/experience-ratings", json={"stars": 5}, headers=auth_headers).status_code == 201


def test_still_blocked_before_30_days(client, db, regular_user, auth_headers):
    client.post("/experience-ratings/dismiss", headers=auth_headers)
    _age_last_rating(db, regular_user.id, days=29)

    assert client.get("/experience-ratings/eligibility", headers=auth_headers).json()["eligible"] is False


def test_cooldown_is_per_user(client, auth_headers):
    client.post("/experience-ratings", json={"stars": 4}, headers=auth_headers)

    client.post("/users", json={"name": "Otro Usuario", "email": "otro@test.com", "password": "PasswordDeTest1!"})
    tokens = client.post("/auth/login", json={"email": "otro@test.com", "password": "PasswordDeTest1!"}).json()
    other_headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    assert client.post("/experience-ratings", json={"stars": 3}, headers=other_headers).status_code == 201


def test_delete_user_removes_ratings(client, db, regular_user, auth_headers):
    client.post("/experience-ratings", json={"stars": 4}, headers=auth_headers)
    user_id = regular_user.id

    assert client.delete("/users/me", headers=auth_headers).status_code == 204
    assert db.query(ExperienceRating).filter(ExperienceRating.user_id == user_id).count() == 0
