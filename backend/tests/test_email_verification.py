"""E-mail service, single-use tokens, verification on sign-up and e-mail change (task 042)."""

import hashlib
from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from app.core.config import Settings
from app.models import models
from app.services import email_service, token_service
from app.services.email_service import _deliver as real_deliver
from tests.conftest import confirm_email, last_token

USER = {"nombre_usuario": "ana", "correo_electronico": "ana@example.com", "password": "StrongPass1"}
INVALID_LINK = "El enlace no es válido o ya venció."
RESEND_ANSWER = "Si el correo tiene una cuenta sin verificar, te enviamos un enlace nuevo."


def _register(client, **changes):
    return client.post("/users/register", json={**USER, **changes})


def _login(client, email=USER["correo_electronico"], password=USER["password"]):
    return client.post("/users/login", data={"username": email, "password": password})


def _sent_to(outbox, address):
    return [message for message in outbox if message["To"] == address]


# --------------------------------------------------------------- email_service


def test_console_backend_logs_instead_of_sending(monkeypatch):
    logged = []
    monkeypatch.setattr(email_service.settings, "email_backend", "console")
    monkeypatch.setattr(email_service.logger, "info", lambda *args: logged.append(args))
    smtp_opened = []
    monkeypatch.setattr(email_service.smtplib, "SMTP", lambda *args, **kwargs: smtp_opened.append(args))

    long_link = "http://localhost:5173/verificar-correo#token=" + "a" * 43
    real_deliver(email_service.build_message("ana@example.com", "Asunto", f"Abre: {long_link}"))

    assert smtp_opened == []
    _template, to, subject, text = logged[0]
    assert (to, subject) == ("ana@example.com", "Asunto")
    # The link stays whole, without quoted-printable soft breaks.
    assert long_link in text


class FakeSMTP:
    instances: list["FakeSMTP"] = []

    def __init__(self, host, port, timeout):
        self.address = (host, port, timeout)
        self.calls = []
        FakeSMTP.instances.append(self)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.calls.append("quit")

    def starttls(self, context):
        self.calls.append("starttls")

    def login(self, user, password):
        self.calls.append(("login", user, password))

    def send_message(self, message):
        self.calls.append(("send", message["To"], message["Subject"]))


def test_smtp_backend_uses_starttls_and_logs_in(monkeypatch):
    FakeSMTP.instances.clear()
    for name, value in {
        "email_backend": "smtp",
        "smtp_host": "smtp.example.com",
        "smtp_port": 587,
        "smtp_user": "usuario",
        "smtp_password": "clave-smtp",
        "email_from": "Predicta <no-responder@example.com>",
    }.items():
        monkeypatch.setattr(email_service.settings, name, value)
    monkeypatch.setattr(email_service.smtplib, "SMTP", FakeSMTP)

    message = email_service.build_message("ana@example.com", "Asunto", "Cuerpo")
    real_deliver(message)

    smtp = FakeSMTP.instances[0]
    assert smtp.address == ("smtp.example.com", 587, email_service.SMTP_TIMEOUT_SECONDS)
    assert smtp.calls == [
        "starttls",
        ("login", "usuario", "clave-smtp"),
        ("send", "ana@example.com", "Asunto"),
        "quit",
    ]
    assert message["From"] == "Predicta <no-responder@example.com>"


PRODUCTION = {
    "database_url": "postgresql+psycopg2://u:p@db.example/predicta?sslmode=require",
    "secret_key": "a" * 32,
    "environment": "production",
    "email_backend": "smtp",
    "smtp_host": "smtp.example.com",
    "smtp_user": "usuario",
    "smtp_password": "clave-smtp",
    "email_from": "Predicta <no-responder@example.com>",
    "frontend_url": "https://predicta.example",
    "_env_file": None,
}


@pytest.mark.parametrize(
    ("changes", "message"),
    [
        ({"smtp_host": None}, "SMTP_HOST"),
        ({"smtp_password": None}, "SMTP_PASSWORD"),
        ({"email_from": None}, "EMAIL_FROM"),
        ({"email_backend": "console"}, "EMAIL_BACKEND=smtp"),
        ({"frontend_url": "http://predicta.example"}, "https://"),
    ],
)
def test_production_refuses_to_start_without_smtp(monkeypatch, changes, message):
    for name in ("SMTP_HOST", "SMTP_USER", "SMTP_PASSWORD", "EMAIL_FROM", "EMAIL_BACKEND", "FRONTEND_URL"):
        monkeypatch.delenv(name, raising=False)
    with pytest.raises(ValidationError, match=message):
        Settings(**{**PRODUCTION, **changes})


def test_production_starts_with_every_smtp_variable():
    assert Settings(**PRODUCTION).email_backend == "smtp"


def test_frontend_url_loses_its_trailing_slash():
    assert Settings(**{**PRODUCTION, "frontend_url": "https://predicta.example/"}).frontend_url == (
        "https://predicta.example"
    )


def test_a_failed_delivery_does_not_fail_the_request(client, monkeypatch):
    def broken(_message):
        raise OSError("SMTP caído")

    monkeypatch.setattr(email_service, "_deliver", broken)

    response = _register(client)

    assert response.status_code == 201


# --------------------------------------------------------------- token_service


def _user_id(test_db, email=USER["correo_electronico"]):
    with test_db() as session:
        return session.query(models.Usuario).filter_by(correo_electronico=email).one().id_usuario


def test_only_the_hash_of_a_token_is_stored(client, test_db):
    assert _register(client).status_code == 201
    raw = last_token(USER["correo_electronico"])

    with test_db() as session:
        stored = session.query(models.TokenUsuario).one()
    assert stored.token_hash == hashlib.sha256(raw.encode()).hexdigest()
    assert raw not in stored.token_hash
    assert stored.tipo == token_service.VERIFICATION


def test_a_token_is_consumed_once(client, test_db):
    assert _register(client).status_code == 201
    user_id = _user_id(test_db)
    with test_db() as session:
        raw = token_service.issue(session, user_id, token_service.PASSWORD_RESET, timedelta(minutes=30))
        session.commit()

        assert token_service.consume(session, raw, token_service.VERIFICATION) is None
        assert token_service.consume(session, raw, token_service.PASSWORD_RESET) is not None
        session.commit()
        assert token_service.consume(session, raw, token_service.PASSWORD_RESET) is None


def test_an_expired_token_is_not_consumed(client, test_db):
    assert _register(client).status_code == 201
    user_id = _user_id(test_db)
    with test_db() as session:
        raw = token_service.issue(session, user_id, token_service.PASSWORD_RESET, timedelta(minutes=30))
        token = session.query(models.TokenUsuario).filter_by(tipo=token_service.PASSWORD_RESET).one()
        token.expira_en = datetime.now(UTC) - timedelta(seconds=1)
        session.commit()

        assert token_service.consume(session, raw, token_service.PASSWORD_RESET) is None


def test_a_new_token_replaces_the_previous_one(client, test_db):
    assert _register(client).status_code == 201
    user_id = _user_id(test_db)
    with test_db() as session:
        first = token_service.issue(session, user_id, token_service.PASSWORD_RESET, timedelta(minutes=30))
        second = token_service.issue(session, user_id, token_service.PASSWORD_RESET, timedelta(minutes=30))
        session.commit()

        assert token_service.consume(session, first, token_service.PASSWORD_RESET) is None
        assert token_service.consume(session, second, token_service.PASSWORD_RESET) is not None


@pytest.mark.parametrize("raw", ["", "x" * 500])
def test_empty_or_oversized_tokens_are_ignored(test_db, raw):
    with test_db() as session:
        assert token_service.consume(session, raw, token_service.VERIFICATION) is None


# --------------------------------------------------------------- sign-up and login


def test_registration_emails_a_link_with_the_token_in_the_fragment(client, outbox):
    response = _register(client, correo_electronico="Ana@Example.com")

    assert response.status_code == 201
    assert response.json()["correo_verificado"] is False
    assert response.json()["correo_pendiente"] is None
    [message] = _sent_to(outbox, "ana@example.com")
    assert message["Subject"] == "Confirma tu correo en Predicta"
    assert "http://localhost:5173/verificar-correo#token=" in message.get_content()


def test_login_without_verification_answers_403(client):
    assert _register(client).status_code == 201

    response = _login(client)

    assert response.status_code == 403
    assert response.json() == {"detail": "Verifica tu correo antes de iniciar sesión."}


def test_wrong_password_on_an_unverified_account_stays_401(client):
    assert _register(client).status_code == 201

    assert _login(client, password="OtraClave9").status_code == 401


def test_confirming_the_link_lets_the_user_in_and_works_once(client):
    assert _register(client).status_code == 201
    token = last_token(USER["correo_electronico"])

    first = client.post("/users/verificacion/confirmar", json={"token": token})
    again = client.post("/users/verificacion/confirmar", json={"token": token})

    assert first.status_code == 200
    assert first.json() == {"message": "Correo confirmado. Ya puedes iniciar sesión."}
    assert again.status_code == 400
    assert again.json() == {"detail": INVALID_LINK}
    login = _login(client)
    assert login.status_code == 200
    me = client.get("/users/me", headers={"Authorization": f"Bearer {login.json()['access_token']}"})
    assert me.json()["correo_verificado"] is True


@pytest.mark.parametrize("token", ["desconocido", "a" * 43])
def test_unknown_token_answers_the_generic_400(client, token):
    response = client.post("/users/verificacion/confirmar", json={"token": token})

    assert response.status_code == 400
    assert response.json() == {"detail": INVALID_LINK}


def test_malformed_token_is_a_422(client):
    assert client.post("/users/verificacion/confirmar", json={"token": "no válido"}).status_code == 422


def test_resend_answers_the_same_and_only_mails_unverified_accounts(client, outbox):
    assert _register(client).status_code == 201
    assert _register(client, nombre_usuario="bea", correo_electronico="bea@example.com").status_code == 201
    confirm_email(client, "bea@example.com")
    outbox.clear()

    answers = [
        client.post("/users/verificacion/reenviar", json={"correo_electronico": email})
        for email in ("ana@example.com", "bea@example.com", "nadie@example.com")
    ]

    assert [answer.status_code for answer in answers] == [200, 200, 200]
    assert {answer.json()["message"] for answer in answers} == {RESEND_ANSWER}
    assert [message["To"] for message in outbox] == ["ana@example.com"]


def test_resending_invalidates_the_previous_link(client):
    assert _register(client).status_code == 201
    old = last_token(USER["correo_electronico"])
    client.post("/users/verificacion/reenviar", json={"correo_electronico": USER["correo_electronico"]})

    assert client.post("/users/verificacion/confirmar", json={"token": old}).status_code == 400
    confirm_email(client, USER["correo_electronico"])


# --------------------------------------------------------------- e-mail change


def _change_email(client, headers, email, password="StrongPass1"):
    body = {"correo_electronico": email}
    if password is not None:
        body["password_actual"] = password
    return client.put("/users/me", headers=headers, json=body)


@pytest.mark.parametrize(
    ("password", "detail"),
    [
        (None, "Escribe tu contraseña actual para cambiar el correo."),
        ("OtraClave9", "La contraseña actual no es correcta."),
    ],
)
def test_changing_the_email_needs_the_current_password(client, auth_headers, password, detail):
    response = _change_email(client, auth_headers, "nuevo@example.com", password)

    assert response.status_code == 400
    assert response.json() == {"detail": detail}
    assert client.get("/users/me", headers=auth_headers).json()["correo_pendiente"] is None


def test_username_change_alone_needs_no_password(client, auth_headers):
    response = client.put("/users/me", headers=auth_headers, json={"nombre_usuario": "otro_nombre"})

    assert response.status_code == 200
    assert response.json()["nombre_usuario"] == "otro_nombre"


def test_same_email_in_other_case_is_not_a_change(client, auth_headers, outbox):
    outbox.clear()
    response = client.put("/users/me", headers=auth_headers, json={"correo_electronico": "TEST@example.com"})

    assert response.status_code == 200
    assert response.json()["correo_pendiente"] is None
    assert outbox == []


def test_new_email_waits_for_its_link(client, auth_headers, user_credentials, outbox):
    outbox.clear()

    response = _change_email(client, auth_headers, "nuevo@example.com")

    assert response.status_code == 200
    assert response.json()["correo_electronico"] == "test@example.com"
    assert response.json()["correo_pendiente"] == "nuevo@example.com"
    [link] = _sent_to(outbox, "nuevo@example.com")
    [notice] = _sent_to(outbox, "test@example.com")
    assert "#token=" in link.get_content()
    assert "nuevo@example.com" in notice.get_content()
    assert "#token=" not in notice.get_content()
    # Until confirmed, the current address still logs in and the new one does not.
    assert _login(client, "test@example.com", user_credentials["password"]).status_code == 200
    assert _login(client, "nuevo@example.com", user_credentials["password"]).status_code == 401

    confirm_email(client, "nuevo@example.com")

    me = client.get("/users/me", headers=auth_headers).json()
    assert me["correo_electronico"] == "nuevo@example.com"
    assert me["correo_pendiente"] is None
    assert _login(client, "nuevo@example.com", user_credentials["password"]).status_code == 200
    assert _login(client, "test@example.com", user_credentials["password"]).status_code == 401


def test_new_email_cannot_belong_to_another_account(client, auth_headers, second_user):
    response = _change_email(client, auth_headers, "second@example.com")

    assert response.status_code == 400
    assert response.json() == {"detail": "El nuevo correo electronico ya esta en uso."}


def test_new_email_cannot_be_pending_on_another_account(client, auth_headers, second_user):
    assert _change_email(client, second_user, "libre@example.com").status_code == 200

    response = _change_email(client, auth_headers, "libre@example.com")

    assert response.status_code == 400
    assert response.json() == {"detail": "El nuevo correo electronico ya esta en uso."}


def test_pending_email_taken_meanwhile_is_dropped_on_confirmation(client, auth_headers):
    assert _change_email(client, auth_headers, "libre@example.com").status_code == 200
    token = last_token("libre@example.com")
    # Someone registers the address before the link is opened.
    assert _register(client, nombre_usuario="rapida", correo_electronico="libre@example.com").status_code == 201

    response = client.post("/users/verificacion/confirmar", json={"token": token})

    assert response.status_code == 400
    me = client.get("/users/me", headers=auth_headers).json()
    assert me["correo_electronico"] == "test@example.com"
    assert me["correo_pendiente"] is None
