import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from app.database import Base, get_db
from app.main import app
from app.limiter import limiter
from app.models.user import User
from pwdlib import PasswordHash
from app.services.auth_service import create_access_token

password_hash = PasswordHash.recommended()

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")

if not TEST_DATABASE_URL:
    raise ValueError("TEST_DATABASE_URL is not defined on the .env")

engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture(scope="function", autouse=True)
def setup_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    app.dependency_overrides[get_db] = override_get_db

    yield

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)
    limiter._storage.reset()

@pytest.fixture()
def client():
    with TestClient(app) as client:
        yield client

@pytest.fixture()
def db():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()

@pytest.fixture()
def regular_user(db):
    user = User(
        name="Regular User",
        email="user@test.com",
        hashed_password=password_hash.hash("UserPass1!"),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@pytest.fixture()
def auth_headers(regular_user):
    token = create_access_token({"sub": str(regular_user.id), "email": regular_user.email})
    return {"Authorization": f"Bearer {token}"}
