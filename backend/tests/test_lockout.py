"""Account lockout after wrong passwords, and the fixed-hash timing guard (task 043)."""

from app.core import security
from app.models import models
from tests.conftest import last_token

LOCKED = {"detail": "Cuenta bloqueada temporalmente. Intenta en unos minutos o restablece tu contraseña."}


def _login(client, password="StrongPass1", email="test@example.com"):
    return client.post("/users/login", data={"username": email, "password": password})


def _fail(client, times):
    return [_login(client, "Equivocada1").status_code for _ in range(times)]


def _failed_attempts(test_db):
    with test_db() as session:
        return session.query(models.Usuario).filter_by(correo_electronico="test@example.com").one().intentos_fallidos


def test_limits_match_the_plan():
    assert security.MAX_FAILED_LOGINS == 10
    assert security.LOCKOUT_MINUTES == 15
    assert security.RESET_TOKEN_MINUTES == 30


def test_a_success_resets_the_counter(client, user_credentials, test_db):
    assert _fail(client, 9) == [401] * 9
    assert _failed_attempts(test_db) == 9

    assert _login(client).status_code == 200

    assert _failed_attempts(test_db) == 0
    assert _fail(client, 9) == [401] * 9


def test_the_tenth_wrong_password_locks_and_mails_a_reset_link(client, user_credentials, outbox):
    outbox.clear()

    statuses = _fail(client, 10)

    assert statuses == [401] * 9 + [423]
    [notice] = outbox
    assert notice["To"] == "test@example.com"
    assert notice["Subject"] == "Bloqueamos tu cuenta de Predicta por seguridad"
    assert "/restablecer-contrasena#token=" in notice.get_content()


def test_the_right_password_is_refused_while_locked(client, user_credentials, clock, outbox):
    _fail(client, 10)
    outbox.clear()

    clock.advance(minutes=security.LOCKOUT_MINUTES - 1)
    response = _login(client)

    assert response.status_code == 423
    assert response.json() == LOCKED
    # Attempts during the lockout neither extend it nor send more mail.
    assert _login(client, "Equivocada1").status_code == 423
    assert outbox == []


def test_the_account_opens_again_after_15_minutes(client, user_credentials, clock, test_db):
    _fail(client, 10)

    clock.advance(minutes=security.LOCKOUT_MINUTES, seconds=1)

    assert _login(client).status_code == 200
    assert _failed_attempts(test_db) == 0


def test_after_a_lockout_the_count_starts_again(client, user_credentials, clock):
    _fail(client, 10)
    clock.advance(minutes=security.LOCKOUT_MINUTES, seconds=1)

    assert _fail(client, 10) == [401] * 9 + [423]


def test_the_reset_link_of_the_notice_lifts_the_lockout(client, user_credentials):
    _fail(client, 10)

    response = client.post(
        "/users/contrasena/restablecer",
        json={"token": last_token("test@example.com"), "password_nueva": "OtraClave9"},
    )

    assert response.status_code == 200
    assert _login(client, "OtraClave9").status_code == 200


def test_unknown_email_still_runs_bcrypt(client, monkeypatch):
    checked = []
    original = security.verify_password

    def spy(password, hashed):
        checked.append(hashed)
        return original(password, hashed)

    monkeypatch.setattr(security, "verify_password", spy)

    response = _login(client, email="nadie@example.com")

    assert response.status_code == 401
    assert response.json() == {"detail": "Credenciales invalidas."}
    assert checked == [security.DUMMY_HASH]
