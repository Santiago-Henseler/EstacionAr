from datetime import datetime, timedelta, UTC

import jwt
import pytest
import repository.reportRepository as reportRepository
from conftest import A_INIT, BASE_PROBA, LEVEL, STREET, headers_for


def _report(client, user_id=1, reason="no_habia_lugar", **extra):
    body = {"street_name": STREET, "level": LEVEL, "reason": reason, **extra}
    return client.post("/reports", json=body, headers=headers_for(user_id))


def _street(client, hour=10):
    response = client.get("/predict/", params={"street_name": STREET, "level": LEVEL, "hour": hour, "depth": 0})
    assert response.status_code == 200
    return response.json()["street"]


def _insert(user_id, minutes_ago, hour=10, reason="no_habia_lugar", status="pendiente"):
    reportRepository.insertReport(
        user_id=user_id,
        reason=reason,
        street_name=STREET,
        level=LEVEL,
        a_init=A_INIT,
        hour=hour,
        status=status,
        created_at=datetime.now(UTC) - timedelta(minutes=minutes_ago),
    )


# --- crear y consultar reportes ---

def test_create_report(client):
    response = _report(client, description="No había nada")
    assert response.status_code == 201
    body = response.json()
    assert body["street_name"] == STREET
    assert body["a_init"] == A_INIT
    assert body["reason"] == "no_habia_lugar"
    assert body["type"] == "mala_indicacion"
    assert body["status"] == "pendiente"
    assert body["description"] == "No había nada"


def test_street_name_is_normalized(client):
    response = client.post(
        "/reports",
        json={"street_name": "  corrientes ", "level": LEVEL, "reason": "otro"},
        headers=headers_for(1),
    )
    assert response.status_code == 201
    assert response.json()["street_name"] == STREET


def test_requires_token(client):
    response = client.post("/reports", json={"street_name": STREET, "level": LEVEL, "reason": "otro"})
    assert response.status_code in (401, 403)
    assert client.get("/reports/me").status_code in (401, 403)


def test_invalid_token(client):
    bad = jwt.encode({"sub": "1"}, "otra-clave-distinta-de-al-menos-32-bytes", algorithm="HS256")
    response = client.get("/reports/me", headers={"Authorization": f"Bearer {bad}"})
    assert response.status_code == 401


def test_unknown_street(client):
    response = client.post(
        "/reports",
        json={"street_name": "NO EXISTE", "level": LEVEL, "reason": "otro"},
        headers=headers_for(1),
    )
    assert response.status_code == 404


def test_invalid_reason(client):
    assert _report(client, reason="cualquiera").status_code == 422


def test_description_max_length(client):
    assert _report(client, description="a" * 280).status_code == 201
    assert _report(client, description="a" * 281).status_code == 422


def test_daily_limit(client):
    for _ in range(10):
        assert _report(client, reason="otro").status_code == 201
    assert _report(client, reason="otro").status_code == 429
    # otro usuario no se ve afectado
    assert _report(client, user_id=2, reason="otro").status_code == 201


def test_daily_limit_resets_after_24h(client):
    for _ in range(10):
        _insert(user_id=1, minutes_ago=25 * 60, reason="otro")
    assert _report(client, reason="otro").status_code == 201


def test_my_reports_only_own(client):
    _report(client, user_id=1)
    _report(client, user_id=1, reason="otro")
    _report(client, user_id=2)

    response = client.get("/reports/me", headers=headers_for(1))
    assert response.status_code == 200
    reports = response.json()
    assert len(reports) == 2
    assert {r["reason"] for r in reports} == {"no_habia_lugar", "otro"}
    assert all(r["status"] == "pendiente" for r in reports)


# --- efecto en la predicción ---

def test_no_reports_keeps_probability(client):
    street = _street(client)
    assert street["probability"] == BASE_PROBA
    assert street["recentReports"] == 0
    assert street["lowAvailability"] is False


def test_one_report_lowers_probability_without_flag(client):
    _report(client, user_id=1)
    street = _street(client)
    assert street["probability"] < BASE_PROBA
    assert street["recentReports"] == 1
    assert street["lowAvailability"] is False


def test_two_users_flag_low_availability(client):
    _report(client, user_id=1)
    one = _street(client)["probability"]
    _report(client, user_id=2)
    street = _street(client)
    assert street["probability"] < one
    assert street["recentReports"] == 2
    assert street["lowAvailability"] is True


def test_same_user_counts_once(client):
    _report(client, user_id=1)
    one = _street(client)
    _report(client, user_id=1)
    twice = _street(client)
    assert twice["recentReports"] == 1
    assert twice["lowAvailability"] is False
    assert twice["probability"] == pytest.approx(one["probability"], abs=1e-4)


def test_live_signal_applies_at_any_hour(client):
    _report(client, user_id=1)
    assert _street(client, hour=3)["probability"] < BASE_PROBA


def test_fresh_report_weighs_more_than_old_one(client):
    _insert(user_id=1, minutes_ago=50, hour=3)
    old = _street(client, hour=10)["probability"]
    _insert(user_id=2, minutes_ago=0, hour=3)
    _insert(user_id=3, minutes_ago=0, hour=3)
    both = _street(client, hour=10)["probability"]
    assert BASE_PROBA > old > both


def test_report_older_than_window_is_not_live(client):
    _insert(user_id=1, minutes_ago=61, hour=3)
    street = _street(client, hour=10)
    assert street["recentReports"] == 0
    assert street["probability"] == BASE_PROBA


def test_historic_same_hour_lowers_probability(client):
    _insert(user_id=1, minutes_ago=24 * 60, hour=10)
    street = _street(client, hour=10)
    assert street["recentReports"] == 0
    assert street["lowAvailability"] is False
    assert street["probability"] < BASE_PROBA


def test_historic_other_hour_does_not_apply(client):
    _insert(user_id=1, minutes_ago=24 * 60, hour=10)
    assert _street(client, hour=15)["probability"] == BASE_PROBA


def test_historic_more_days_lower_more(client):
    _insert(user_id=1, minutes_ago=24 * 60, hour=10)
    one_day = _street(client, hour=10)["probability"]
    _insert(user_id=1, minutes_ago=2 * 24 * 60, hour=10)
    two_days = _street(client, hour=10)["probability"]
    assert two_days < one_day


def test_historic_same_user_same_day_counts_once(client):
    _insert(user_id=1, minutes_ago=24 * 60, hour=10)
    once = _street(client, hour=10)["probability"]
    _insert(user_id=1, minutes_ago=24 * 60 + 5, hour=10)
    assert _street(client, hour=10)["probability"] == once


def test_historic_older_than_90_days_ignored(client):
    _insert(user_id=1, minutes_ago=91 * 24 * 60, hour=10)
    assert _street(client, hour=10)["probability"] == BASE_PROBA


def test_other_reasons_do_not_affect_probability(client):
    for uid, reason in enumerate(["zona_prohibida", "zona_inaccesible", "otro"], start=1):
        assert _report(client, user_id=uid, reason=reason).status_code == 201
    street = _street(client)
    assert street["probability"] == BASE_PROBA
    assert street["recentReports"] == 0


def test_rejected_reports_do_not_count(client):
    _insert(user_id=1, minutes_ago=0, status="rechazado")
    _insert(user_id=2, minutes_ago=24 * 60, hour=10, status="rechazado")
    street = _street(client, hour=10)
    assert street["probability"] == BASE_PROBA
    assert street["recentReports"] == 0
