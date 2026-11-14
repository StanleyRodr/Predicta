"""Session revocation, password change and password reset by e-mail (task 043)."""

from datetime import UTC, datetime, timedelta

import jwt
import pytest

from app.core import security
from app.models import models
from tests.conftest import last_token

NEW_PASSWORD = "OtraClave9"
FORGOT_ANSWER = "Si el correo tiene una cuenta, te enviamos un enlace para elegir una contraseña nueva."
INVALID_LINK = "El enlace no es válido o ya venció."


def _login(client, email="test@example.com", password="StrongPass1"):
    return client.post("/users/login", data={"username": email, "password": password})


def _bearer(token):
    return {"Authorization": f"Bearer {token}"}


def _user(test_db, email="test@example.com"):
    with test_db() as session:
        return session.query(models.Usuario).filter_by(correo_electronico=email).one()


def _forged(claims):
    exp = datetime.now(UTC) + timedelta(minutes=5)
    return jwt.encode({**claims, "exp": exp}, security.SECRET_KEY, algorithm=security.ALGORITHM)


def _change(client, headers, actual="StrongPass1", nueva=NEW_PASSWORD):
    return client.put(
        "/users/me/password", headers=headers, json={"password_actual": actual, "password_nueva": nueva}
    )


def _forgot(client, email="test@example.com"):
    return client.post("/users/contrasena/olvido", json={"correo_electronico": email})


def _reset(client, token, password=NEW_PASSWORD):
    return client.post("/users/contrasena/restablecer", json={"token": token, "password_nueva": password})


def _reset_token(email="test@example.com"):
    return last_token(email)


# --------------------------------------------------------------- revocation


def test_login_token_carries_the_current_version(client, user_credentials, test_db):
    token = _login(client).json()["access_token"]

    claims = jwt.decode(token, security.SECRET_KEY, algorithms=[security.ALGORITHM])

    assert claims["ver"] == _user(test_db).version_token == 0


@pytest.mark.parametrize(
    "extra",
    [{}, {"ver": 1}, {"ver": "0"}, {"ver": None}, {"ver": False}],
    ids=["sin-ver", "ver-vieja", "ver-texto", "ver-nula", "ver-bool"],
)
def test_token_without_the_current_version_is_rejected(client, user_credentials, test_db, extra):
    user_id = _user(test_db).id_usuario

    response = client.get("/users/me", headers=_bearer(_forged({"sub": str(user_id), **extra})))

    assert response.status_code == 401


def test_token_with_the_current_version_is_accepted(client, user_credentials, test_db):
    user_id = _user(test_db).id_usuario

    response = client.get("/users/me", headers=_bearer(_forged({"sub": str(user_id), "ver": 0})))

    assert response.status_code == 200


# --------------------------------------------------------------- change


def test_change_needs_the_right_current_password(client, auth_headers):
    response = _change(client, auth_headers, actual="Equivocada1")

    assert response.status_code == 400
    assert response.json() == {"detail": "La contraseña actual no es correcta."}


def test_new_password_must_differ_from_the_current_one(client, auth_headers):
    response = _change(client, auth_headers, nueva="StrongPass1")

    assert response.status_code == 400
    assert response.json() == {"detail": "La contraseña nueva debe ser distinta de la actual."}


def test_new_password_follows_the_password_rules(client, auth_headers):
    response = _change(client, auth_headers, nueva="debil")

    assert response.status_code == 422
    assert "debil" not in response.text


def test_change_returns_a_working_token_and_closes_other_sessions(client, auth_headers, outbox):
    other_session = _bearer(_login(client).json()["access_token"])
    outbox.clear()

    response = _change(client, auth_headers)

    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"
    new_headers = _bearer(response.json()["access_token"])
    assert client.get("/users/me", headers=new_headers).status_code == 200
    assert client.get("/users/me", headers=auth_headers).status_code == 401
    assert client.get("/users/me", headers=other_session).status_code == 401
    [notice] = outbox
    assert notice["To"] == "test@example.com"
    assert notice["Subject"] == "Tu contraseña de Predicta cambió"
    assert _login(client, password=NEW_PASSWORD).status_code == 200
    assert _login(client).status_code == 401


def test_change_needs_a_session(client):
    assert _change(client, {}).status_code == 401


# --------------------------------------------------------------- forgot and reset


def test_forgot_answers_the_same_and_only_mails_existing_accounts(client, user_credentials, outbox):
    outbox.clear()

    known = _forgot(client)
    unknown = _forgot(client, "nadie@example.com")

    assert known.status_code == unknown.status_code == 200
    assert known.json() == unknown.json() == {"message": FORGOT_ANSWER}
    [message] = outbox
    assert message["To"] == "test@example.com"
    assert message["Subject"] == "Restablece tu contraseña de Predicta"
    assert "http://localhost:5173/restablecer-contrasena#token=" in message.get_content()


def test_reset_sets_the_password_and_closes_every_session(client, auth_headers):
    _forgot(client)

    response = _reset(client, _reset_token())

    assert response.status_code == 200
    assert response.json() == {"message": "Contraseña actualizada. Ya puedes iniciar sesión."}
    assert client.get("/users/me", headers=auth_headers).status_code == 401
    assert _login(client, password=NEW_PASSWORD).status_code == 200
    assert _login(client).status_code == 401


def test_a_reset_link_works_once(client, user_credentials):
    _forgot(client)
    token = _reset_token()

    assert _reset(client, token).status_code == 200
    again = _reset(client, token, password="TerceraClave7")

    assert again.status_code == 400
    assert again.json() == {"detail": INVALID_LINK}


def test_a_reset_link_expires_after_30_minutes(client, user_credentials, clock):
    _forgot(client)
    token = _reset_token()

    clock.advance(minutes=security.RESET_TOKEN_MINUTES, seconds=1)

    assert _reset(client, token).status_code == 400
    assert _login(client).status_code == 200


def test_a_reset_link_still_works_before_30_minutes(client, user_credentials, clock):
    _forgot(client)
    token = _reset_token()

    clock.advance(minutes=security.RESET_TOKEN_MINUTES - 1)

    assert _reset(client, token).status_code == 200


def test_a_new_request_invalidates_the_previous_link(client, user_credentials):
    _forgot(client)
    first = _reset_token()
    _forgot(client)

    assert _reset(client, first).status_code == 400
    assert _reset(client, _reset_token()).status_code == 200


def test_a_verification_link_does_not_reset_the_password(client):
    credentials = {"nombre_usuario": "nueva", "correo_electronico": "nueva@example.com", "password": "StrongPass1"}
    assert client.post("/users/register", json=credentials).status_code == 201

    assert _reset(client, last_token("nueva@example.com")).status_code == 400


def test_reset_verifies_the_email(client):
    credentials = {"nombre_usuario": "nueva", "correo_electronico": "nueva@example.com", "password": "StrongPass1"}
    assert client.post("/users/register", json=credentials).status_code == 201
    assert _login(client, "nueva@example.com").status_code == 403
    _forgot(client, "nueva@example.com")

    assert _reset(client, _reset_token("nueva@example.com")).status_code == 200

    assert _login(client, "nueva@example.com", NEW_PASSWORD).status_code == 200


def test_reset_password_follows_the_password_rules(client, user_credentials):
    _forgot(client)

    assert _reset(client, _reset_token(), password="debil").status_code == 422
