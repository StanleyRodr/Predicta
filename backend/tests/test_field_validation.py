"""Field rules shared by the API and the frontend (task 040)."""

import io

import pytest
from openpyxl import load_workbook

from app.schemas import schemas
from app.services.report_service import neutralize_formula
from tests.conftest import confirm_email

VALID_USER = {
    "nombre_usuario": "ana_maria",
    "correo_electronico": "ana@example.com",
    "password": "StrongPass1",
}


def _register(client, **changes):
    return client.post("/users/register", json={**VALID_USER, **changes})


def _upload_csv(client, headers, body: bytes):
    return client.post(
        "/etl/upload-ventas",
        headers=headers,
        files={"file": ("ventas.csv", body, "text/csv")},
    )


# ---------------------------------------------------------------- registration


@pytest.mark.parametrize(
    "nombre",
    ["ana", "Ana María", "josé.pérez-2", "user_01", "  padded name  ", "x" * 50],
)
def test_register_accepts_valid_usernames(client, nombre):
    response = _register(client, nombre_usuario=nombre)

    assert response.status_code == 201
    assert response.json()["nombre_usuario"] == nombre.strip()


@pytest.mark.parametrize(
    "nombre",
    ["ab", "x" * 51, "ana<script>", "ana;drop", "tab\there", "nul\x00name", "a@b", "   "],
)
def test_register_rejects_invalid_usernames(client, nombre):
    assert _register(client, nombre_usuario=nombre).status_code == 422


def test_register_rejects_email_over_100_characters(client):
    local = "a" * 64
    domain = "b" * 40 + ".com"  # 64 + 1 + 44 = 109 characters
    assert _register(client, correo_electronico=f"{local}@{domain}").status_code == 422


@pytest.mark.parametrize("email", ["sin-arroba", "a@", "@example.com"])
def test_register_rejects_malformed_email(client, email):
    assert _register(client, correo_electronico=email).status_code == 422


@pytest.mark.parametrize(
    "password",
    [
        "Corta1",  # under 8 characters
        "sinmayuscula1",
        "SINMINUSCULA1",
        "SinDigitoAqui",
        "Aa1" + "x" * 70,  # 73 bytes
        "Aa1" + "ñ" * 35,  # 73 bytes in UTF-8, 38 characters
        "Tab\tPass1x",  # control character
    ],
)
def test_register_rejects_invalid_passwords(client, password):
    assert _register(client, password=password).status_code == 422


def test_register_accepts_password_of_exactly_72_bytes(client):
    assert _register(client, password="Aa1" + "x" * 69).status_code == 201


# ---------------------------------------------------------------- email case


def test_register_stores_email_trimmed_and_lowercase(client):
    response = _register(client, correo_electronico="  Ana@Example.COM ")

    assert response.status_code == 201
    assert response.json()["correo_electronico"] == "ana@example.com"


def test_register_rejects_same_email_with_other_case(client):
    assert _register(client, correo_electronico="ana@example.com").status_code == 201

    duplicate = _register(client, nombre_usuario="otra_ana", correo_electronico="ANA@example.com")

    assert duplicate.status_code == 400


def test_login_ignores_email_case(client):
    assert _register(client).status_code == 201
    confirm_email(client, "ana@example.com")

    login = client.post(
        "/users/login",
        data={"username": " ANA@Example.com ", "password": VALID_USER["password"]},
    )

    assert login.status_code == 200


def test_profile_update_lowercases_email(client, auth_headers, user_credentials):
    response = client.put(
        "/users/me",
        headers=auth_headers,
        json={"correo_electronico": "Nuevo@Example.com", "password_actual": user_credentials["password"]},
    )

    assert response.status_code == 200
    # The new address waits for its link (task 042), already lowercased.
    assert response.json()["correo_pendiente"] == "nuevo@example.com"


def test_profile_update_rejects_invalid_username(client, auth_headers):
    response = client.put("/users/me", headers=auth_headers, json={"nombre_usuario": "a<b>c"})

    assert response.status_code == 422


# ---------------------------------------------------------------- 422 without echo


def test_validation_error_does_not_echo_the_password(client):
    response = _register(client, password="secretoDebil")

    assert response.status_code == 422
    assert "secretoDebil" not in response.text
    for error in response.json()["detail"]:
        assert set(error) <= {"loc", "msg", "type"}


# ---------------------------------------------------------------- query and path params


@pytest.mark.parametrize(
    ("path", "params"),
    [
        ("/analytics/forecast", {"categoria": "c" * 101}),
        ("/analytics/forecast", {"categoria": "Abarrotes", "producto": "p" * 151}),
        ("/analytics/ventas", {"categoria": "c" * 101}),
        ("/analytics/stats/series", {"categoria": "c" * 101}),
        ("/analytics/productos", {"categoria": "c" * 101}),
        ("/analytics/forecast", {"categoria": "Aba\x01rrotes"}),
        ("/analytics/ventas", {"categoria": "Abarrotes", "producto": "Pan\x7f"}),
    ],
)
def test_text_params_are_bounded(client, auth_headers, path, params):
    assert client.get(path, headers=auth_headers, params=params).status_code == 422


def test_category_path_param_is_bounded(client, auth_headers):
    response = client.get(f"/analytics/prediccion-categorias/{'c' * 101}", headers=auth_headers)

    assert response.status_code == 422


def test_month_path_param_is_bounded(client, auth_headers):
    response = client.get(f"/analytics/reporte-mensual/{'m' * 21}", headers=auth_headers)

    assert response.status_code == 422


def test_save_prediction_rejects_control_characters(client, auth_headers):
    response = client.post(
        "/analytics/predicciones", headers=auth_headers, json={"categoria": "Aba\x00rrotes"}
    )

    assert response.status_code == 422


# ---------------------------------------------------------------- ETL


def test_upload_rejects_rows_with_control_characters(client, auth_headers):
    body = (
        b"producto,monto,categoria,fecha\n"
        b"Pan\x00,10,Panaderia,2026-01-10\n"
        b"Leche,18,Lac\x01teos,2026-01-11\n"
        b"Arroz,25,Abarrotes,2026-01-12\n"
    )

    response = _upload_csv(client, auth_headers, body)

    assert response.status_code == 200
    data = response.json()
    assert data["registros_cargados"] == 1
    assert data["filas_rechazadas"] == 2
    messages = " ".join(error["error"] for error in data["errores"])
    assert "caracteres de control" in messages


# ---------------------------------------------------------------- Excel


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("=1+1", "'=1+1"),
        ("+5", "'+5"),
        ("-X", "'-X"),
        ("@A", "'@A"),
        ("\tTab", "'\tTab"),
        ("\rRet", "'\rRet"),
        ("Arroz", "Arroz"),
        ("", ""),
        (None, None),
        (-5.0, -5.0),
        (12, 12),
    ],
)
def test_neutralize_formula(value, expected):
    assert neutralize_formula(value) == expected


def test_excel_export_neutralizes_formulas(client, auth_headers):
    body = (
        b"producto,monto,categoria,fecha\n"
        b'"=HYPERLINK(""http://x"")",10,=1+1,2026-01-10\n'
        b"+5,1234.5,@Cat,2026-01-11\n"
    )
    assert _upload_csv(client, auth_headers, body).json()["registros_cargados"] == 2

    response = client.get("/analytics/export/excel", headers=auth_headers)

    worksheet = load_workbook(io.BytesIO(response.content)).active
    products = {worksheet[f"B{row}"].value for row in (2, 3)}
    categories = {worksheet[f"D{row}"].value for row in (2, 3)}
    amounts = {worksheet[f"C{row}"].value for row in (2, 3)}
    assert all(str(value).startswith("'") for value in products | categories)
    assert all(worksheet[f"B{row}"].data_type == "s" for row in (2, 3))
    assert amounts == {10, 1234.5}


def test_limits_match_database_columns():
    from app.models import models

    columns = models.Usuario.__table__.columns
    assert columns["nombre_usuario"].type.length == schemas.MAX_USERNAME_LENGTH
    assert columns["correo_electronico"].type.length == schemas.MAX_EMAIL_LENGTH
    venta = models.Venta.__table__.columns
    assert venta["producto"].type.length == schemas.MAX_PRODUCT_LENGTH
    assert venta["categoria"].type.length == schemas.MAX_CATEGORY_LENGTH
