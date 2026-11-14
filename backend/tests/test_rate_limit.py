"""Per-route and global rate limits, the Spanish 429, and the client IP behind proxies.

The ``client`` fixture disables the limiter; ``rate_limited`` turns it back on
for one test, with empty counters.
"""

import pytest
from fastapi.testclient import TestClient

from app.core import rate_limit
from app.core.rate_limit import limiter
from app.main import app

CSV = b"producto,monto,categoria,fecha\nArroz,25.50,Abarrotes,2026-01-10\n"


@pytest.fixture
def rate_limited(client, auth_headers):
    """Enable the limiter after the test user exists, so its sign-up is not counted."""
    limiter.reset()
    limiter.enabled = True
    try:
        yield auth_headers
    finally:
        limiter.enabled = False
        limiter.reset()


def _register(http, number, **headers):
    return http.post(
        "/users/register",
        json={
            "nombre_usuario": f"usuario{number}",
            "correo_electronico": f"usuario{number}@example.com",
            "password": "StrongPass1",
        },
        headers=headers,
    )


def _limit(value: str) -> int:
    return int(value.split("/")[0])


def _assert_too_many(response):
    assert response.status_code == 429
    assert response.json() == {"detail": "Demasiadas solicitudes. Intenta de nuevo en un momento."}
    assert 1 <= int(response.headers["Retry-After"]) <= 60


def test_limits_match_the_plan():
    assert rate_limit.LOGIN_LIMIT == "5/minute"
    assert rate_limit.REGISTER_LIMIT == "3/minute"
    assert rate_limit.UPLOAD_LIMIT == "10/minute"
    assert rate_limit.COMPUTE_LIMIT == "20/minute"
    assert rate_limit.GLOBAL_LIMIT == "120/minute"
    assert rate_limit.RESEND_VERIFICATION_LIMIT == "3/minute"
    assert rate_limit.CONFIRM_LINK_LIMIT == "10/minute"
    assert rate_limit.PASSWORD_CHANGE_LIMIT == "5/minute"
    assert rate_limit.FORGOT_PASSWORD_LIMIT == "3/minute"
    assert rate_limit.RESET_PASSWORD_LIMIT == "10/minute"


def test_fourth_registration_in_a_minute_is_rejected(client, rate_limited):
    for number in range(3):
        assert _register(client, number).status_code == 201
    _assert_too_many(_register(client, 3))


def test_sixth_login_in_a_minute_is_rejected(client, rate_limited):
    form = {"username": "test@example.com", "password": "Wrong1234"}
    for _ in range(_limit(rate_limit.LOGIN_LIMIT)):
        assert client.post("/users/login", data=form).status_code == 401
    _assert_too_many(client.post("/users/login", data=form))


@pytest.mark.parametrize(
    ("path", "body", "limit"),
    [
        ("/users/verificacion/reenviar", {"correo_electronico": "nadie@example.com"}, rate_limit.RESEND_VERIFICATION_LIMIT),
        ("/users/verificacion/confirmar", {"token": "desconocido"}, rate_limit.CONFIRM_LINK_LIMIT),
        ("/users/contrasena/olvido", {"correo_electronico": "nadie@example.com"}, rate_limit.FORGOT_PASSWORD_LIMIT),
        (
            "/users/contrasena/restablecer",
            {"token": "desconocido", "password_nueva": "OtraClave9"},
            rate_limit.RESET_PASSWORD_LIMIT,
        ),
    ],
)
def test_verification_routes_are_limited(client, rate_limited, path, body, limit):
    for _ in range(_limit(limit)):
        assert client.post(path, json=body).status_code != 429
    _assert_too_many(client.post(path, json=body))


@pytest.mark.parametrize("path", ["/etl/analizar-columnas", "/etl/upload-ventas"])
def test_uploads_are_limited(client, rate_limited, path):
    def send():
        return client.post(path, headers=rate_limited, files={"file": ("v.csv", CSV, "text/csv")})

    for _ in range(_limit(rate_limit.UPLOAD_LIMIT)):
        assert send().status_code != 429
    _assert_too_many(send())


@pytest.mark.parametrize(
    "method_path",
    [
        ("GET", "/analytics/predict"),
        ("GET", "/analytics/forecast"),
        ("POST", "/analytics/predicciones"),
        ("GET", "/analytics/export/excel"),
        ("GET", "/analytics/export/pdf"),
        ("GET", "/analytics/reporte-predictivo-anual-pdf"),
        ("GET", "/analytics/reporte-mensual/{n}"),
        ("GET", "/analytics/prediccion-categorias/{n}"),
    ],
)
def test_forecasts_and_reports_are_limited(client, rate_limited, method_path):
    method, path = method_path

    def send(number):
        # A different path parameter each time still shares one counter.
        return client.request(method, path.format(n=f"x{number}"), headers=rate_limited, json={})

    for number in range(_limit(rate_limit.COMPUTE_LIMIT)):
        assert send(number).status_code != 429
    _assert_too_many(send(99))


@pytest.mark.parametrize("path", ["/health", "/analytics/stats"])
def test_other_routes_share_the_global_limit(client, rate_limited, path):
    for _ in range(_limit(rate_limit.GLOBAL_LIMIT)):
        assert client.get(path, headers=rate_limited).status_code != 429
    _assert_too_many(client.get(path, headers=rate_limited))


def test_disabled_limiter_never_answers_429(client):
    assert not limiter.enabled
    for number in range(5):
        assert _register(client, number).status_code == 201


def test_trusted_proxy_gives_each_client_its_own_counter(client, rate_limited):
    behind_proxy = TestClient(app, client=("127.0.0.1", 50000))
    for number in range(3):
        assert _register(behind_proxy, number, **{"X-Forwarded-For": "198.51.100.1"}).status_code == 201

    _assert_too_many(_register(behind_proxy, 3, **{"X-Forwarded-For": "198.51.100.1"}))
    assert _register(behind_proxy, 4, **{"X-Forwarded-For": "198.51.100.2"}).status_code == 201


def test_untrusted_sender_cannot_choose_its_ip(client, rate_limited):
    direct = TestClient(app, client=("203.0.113.5", 50000))
    for number in range(3):
        forged = {"X-Forwarded-For": f"198.51.100.{number}"}
        assert _register(direct, number, **forged).status_code == 201

    _assert_too_many(_register(direct, 3, **{"X-Forwarded-For": "198.51.100.200"}))


def test_password_change_is_limited(client, rate_limited):
    body = {"password_actual": "Equivocada1", "password_nueva": "OtraClave9"}
    for _ in range(_limit(rate_limit.PASSWORD_CHANGE_LIMIT)):
        assert client.put("/users/me/password", headers=rate_limited, json=body).status_code == 400
    _assert_too_many(client.put("/users/me/password", headers=rate_limited, json=body))
