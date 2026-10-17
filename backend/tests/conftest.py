"""Shared pytest fixtures and configuration."""

import os

# Keep tests isolated from a developer's database. The application imports its
# engine at module load time, so configure SQLite before importing the app.
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ.setdefault("SECRET_KEY", "test-secret-key")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.core.rate_limit import limiter
from app.main import app


@pytest.fixture(scope="function")
def test_db():
    """Provide an in-memory SQLite database for tests."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    yield TestingSessionLocal
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(test_db):
    """Provide a TestClient with overridden database dependency."""
    def override_get_db():
        db = test_db()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    limiter.enabled = False
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        limiter.enabled = True
        app.dependency_overrides.clear()


@pytest.fixture
def user_credentials(client):
    """Create and authenticate an isolated test user."""
    credentials = {
        "nombre_usuario": "test_user",
        "correo_electronico": "test@example.com",
        "password": "StrongPass1",
    }
    response = client.post("/users/register", json=credentials)
    assert response.status_code == 201

    login = client.post(
        "/users/login",
        data={"username": credentials["correo_electronico"], "password": credentials["password"]},
    )
    assert login.status_code == 200
    return credentials


@pytest.fixture
def auth_headers(client, user_credentials):
    """Return Bearer headers for the isolated test user."""
    login = client.post(
        "/users/login",
        data={
            "username": user_credentials["correo_electronico"],
            "password": user_credentials["password"],
        },
    )
    assert login.status_code == 200
    return {"Authorization": f"Bearer {login.json()['access_token']}"}
