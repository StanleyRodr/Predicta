"""Tests for authentication endpoints."""

def test_register_success(client):
    response = client.post(
        "/users/register",
        json={
            "nombre_usuario": "nuevo_usuario",
            "correo_electronico": "nuevo@example.com",
            "password": "StrongPass1",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["nombre_usuario"] == "nuevo_usuario"
    assert body["correo_electronico"] == "nuevo@example.com"
    assert "password" not in body


def test_register_duplicate_email_returns_bad_request(client):
    payload = {
        "nombre_usuario": "primer_usuario",
        "correo_electronico": "same@example.com",
        "password": "StrongPass1",
    }
    assert client.post("/users/register", json=payload).status_code == 201

    duplicate = {**payload, "nombre_usuario": "segundo_usuario"}
    response = client.post("/users/register", json=duplicate)

    assert response.status_code == 400
    assert "correo" in response.json()["detail"]


def test_register_weak_password_returns_unprocessable_entity(client):
    response = client.post(
        "/users/register",
        json={
            "nombre_usuario": "usuario_debil",
            "correo_electronico": "debil@example.com",
            "password": "weak",
        },
    )

    assert response.status_code == 422


def test_login_success_returns_bearer_token(client, user_credentials):
    response = client.post(
        "/users/login",
        data={
            "username": user_credentials["correo_electronico"],
            "password": user_credentials["password"],
        },
    )

    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"
    assert response.json()["access_token"]


def test_login_invalid_credentials_returns_unauthorized(client, user_credentials):
    response = client.post(
        "/users/login",
        data={
            "username": user_credentials["correo_electronico"],
            "password": "WrongPass1",
        },
    )

    assert response.status_code == 401


def test_me_without_token_returns_unauthorized(client):
    response = client.get("/users/me")

    assert response.status_code == 401


def test_me_with_valid_token_returns_current_user(client, auth_headers):
    response = client.get("/users/me", headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["correo_electronico"] == "test@example.com"


def test_update_profile_returns_updated_user(client, auth_headers):
    response = client.put(
        "/users/me",
        headers=auth_headers,
        json={"nombre_usuario": "usuario_actualizado"},
    )

    assert response.status_code == 200
    assert response.json()["nombre_usuario"] == "usuario_actualizado"
