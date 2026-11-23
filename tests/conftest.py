import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
os.chdir(ROOT)  # main.py carga modelo_estacionar.pkl desde la raíz

os.environ["FEEDBACK_DB"] = os.path.join(tempfile.mkdtemp(), "feedBack.db")
os.environ["SECRET_KEY"] = "test-secret-key-de-al-menos-32-bytes"
os.environ["ALGORITHM"] = "HS256"

import jwt
import pytest
from fastapi.testclient import TestClient

import main
import repository.feedBackRepository as feedBackRepository
import repository.reportRepository as reportRepository
import service.predictSrevice as predictSrevice

BASE_PROBA = 0.5
STREET = "CORRIENTES"
LEVEL = 1051  # cae en el tramo 1001-1099 (impar)
A_INIT = 1001

STREET_DOC = {
    "_id": STREET,
    "streets": {
        str(A_INIT): {
            "aFin": 1099,
            "rule": 1,
            "hInit": 0,
            "hFin": 23,
            "latitudeInit": -34.60,
            "longitudeInit": -58.38,
            "latitudeEnd": -34.61,
            "longitudeEnd": -58.39,
            "neighbors": {},
        }
    },
}


@pytest.fixture(autouse=True)
def isolated(tmp_path, monkeypatch):
    db_path = str(tmp_path / "test.db")
    monkeypatch.setattr(feedBackRepository, "DATABASE", db_path)
    monkeypatch.setattr(reportRepository, "DATABASE", db_path)
    feedBackRepository.setFeedBackDataBase()
    reportRepository.setReportsDataBase()

    monkeypatch.setattr(predictSrevice, "getRuledStreet", lambda name: STREET_DOC if name.strip().upper() == STREET else None)
    monkeypatch.setattr(predictSrevice, "predict", lambda street, aInit, aFin, hour: BASE_PROBA)


@pytest.fixture()
def client():
    with TestClient(main.app) as c:
        yield c


def headers_for(user_id: int) -> dict:
    token = jwt.encode({"sub": str(user_id)}, "test-secret-key-de-al-menos-32-bytes", algorithm="HS256")
    return {"Authorization": f"Bearer {token}"}
