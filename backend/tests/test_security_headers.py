"""Security headers on every response, Swagger hidden in production, and the root banner."""

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app

BASE_HEADERS = {
    "x-content-type-options": "nosniff",
    "x-frame-options": "DENY",
    "referrer-policy": "no-referrer",
    "content-security-policy": "default-src 'none'; frame-ancestors 'none'",
}


@pytest.fixture
def production_client():
    config = Settings(
        database_url="postgresql+psycopg2://u:p@db.example/predicta?sslmode=require",
        secret_key="a" * 32,
        environment="production",
        cors_origins="https://predicta.example",
        email_backend="smtp",
        smtp_host="smtp.example.com",
        smtp_user="usuario",
        smtp_password="clave-smtp",
        email_from="Predicta <no-responder@example.com>",
        frontend_url="https://predicta.example",
        _env_file=None,
    )
    # Without ``with``, the lifespan (and its database check) does not run.
    return TestClient(create_app(config))


def _assert_base_headers(response):
    for name, value in BASE_HEADERS.items():
        assert response.headers.get(name) == value, name


@pytest.mark.parametrize("path", ["/health", "/", "/no-existe"])
def test_public_responses_carry_the_headers(client, path):
    response = client.get(path)
    _assert_base_headers(response)
    assert "cache-control" not in response.headers


def test_private_responses_are_not_stored(client, auth_headers):
    response = client.get("/users/me", headers=auth_headers)
    assert response.status_code == 200
    _assert_base_headers(response)
    assert response.headers["cache-control"] == "no-store"


@pytest.mark.parametrize(
    ("method", "path", "status"),
    [("GET", "/users/me", 401), ("POST", "/users/register", 422), ("GET", "/analytics/stats", 401)],
)
def test_error_responses_carry_the_headers(client, method, path, status):
    response = client.request(method, path, json={})
    assert response.status_code == status
    _assert_base_headers(response)
    assert response.headers["cache-control"] == "no-store"


def test_hsts_only_in_production(client, production_client):
    assert "strict-transport-security" not in client.get("/health").headers
    response = production_client.get("/health")
    assert response.headers["strict-transport-security"] == "max-age=31536000; includeSubDomains"
    _assert_base_headers(response)


@pytest.mark.parametrize("path", ["/docs", "/redoc", "/openapi.json"])
def test_swagger_is_hidden_in_production(production_client, path):
    response = production_client.get(path)
    assert response.status_code == 404
    _assert_base_headers(response)


@pytest.mark.parametrize("path", ["/docs", "/redoc"])
def test_swagger_works_outside_production_without_the_strict_csp(client, path):
    response = client.get(path)
    assert response.status_code == 200
    assert "content-security-policy" not in response.headers
    assert response.headers["x-content-type-options"] == "nosniff"


def test_root_answers_in_development_with_the_docs_path(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"service": "Predicta API", "version": "0.2.0", "docs": "/docs"}


def test_root_answers_in_production_without_the_docs_path(production_client):
    response = production_client.get("/")
    assert response.status_code == 200
    assert response.json() == {"service": "Predicta API", "version": "0.2.0"}
