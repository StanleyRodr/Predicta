"""Tests for ETL limits, number parsing, SQL parsing, and duplicate files."""

import io
import threading
import zipfile

import pandas as pd
import pytest

from app.api import etl_routes
from app.models import models

HEADER = b"producto,monto,categoria,fecha\n"


def _upload(client, headers, contents, name="ventas.csv"):
    return client.post(
        "/etl/upload-ventas",
        headers=headers,
        files={"file": (name, contents, "application/octet-stream")},
    )


def _sales(test_db):
    session = test_db()
    try:
        return session.query(models.Venta).order_by(models.Venta.id_venta).all()
    finally:
        session.close()


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("1234.56", 1234.56),
        ("1,234", 1234.0),
        ("1,234,567.89", 1234567.89),
        ("45,95", 45.95),
        ("45,9", 45.9),
    ],
)
def test_parse_amount_accepts_documented_formats(value, expected):
    assert etl_routes._parse_amount(value) == expected


@pytest.mark.parametrize("value", ["1.234,56", "1234,567", "12,34,567", "0,123", "abc"])
def test_parse_amount_rejects_ambiguous_formats(value):
    with pytest.raises(etl_routes.RowValidationError):
        etl_routes._parse_amount(value)


def test_parse_amount_keeps_numeric_spreadsheet_cells():
    assert etl_routes._parse_amount(1234.5) == 1234.5


def test_parse_quantity_uses_the_same_number_rules():
    assert etl_routes._parse_quantity("1,234") == 1234.0


@pytest.mark.parametrize("amount", ["-5", "0", "1e9", "100000000"])
def test_out_of_range_amount_rejects_only_its_row(client, auth_headers, test_db, amount):
    contents = HEADER + f"Malo,{amount},Abarrotes,2026-01-01\n".encode()
    contents += b"Bueno,10,Abarrotes,2026-01-02\n"

    response = _upload(client, auth_headers, contents)

    assert response.status_code == 200
    body = response.json()
    assert body["registros_cargados"] == 1
    assert body["errores"][0]["fila"] == 2
    assert [sale.producto for sale in _sales(test_db)] == ["Bueno"]


def test_too_long_text_rejects_only_its_row(client, auth_headers):
    contents = HEADER + b"P" * 151 + b",10,Abarrotes,2026-01-01\n"
    contents += b"Bueno,10," + b"C" * 101 + b",2026-01-02\nOtro,10,Bebidas,2026-01-03\n"

    response = _upload(client, auth_headers, contents)

    assert response.json()["registros_cargados"] == 1
    assert [error["fila"] for error in response.json()["errores"]] == [2, 3]


def test_oversized_file_is_rejected(client, auth_headers, monkeypatch):
    monkeypatch.setattr(etl_routes, "MAX_UPLOAD_BYTES", 10)
    monkeypatch.setattr(etl_routes, "READ_CHUNK_BYTES", 4)

    response = _upload(client, auth_headers, HEADER)

    assert response.status_code == 413


def test_too_many_csv_rows_are_rejected(client, auth_headers, monkeypatch):
    monkeypatch.setattr(etl_routes, "MAX_ROWS", 1)
    contents = HEADER + b"A,1,X,2026-01-01\nB,2,X,2026-01-02\n"

    response = _upload(client, auth_headers, contents)

    assert response.status_code == 413


def test_too_many_xlsx_rows_are_rejected(client, auth_headers, monkeypatch):
    monkeypatch.setattr(etl_routes, "MAX_ROWS", 1)
    output = io.BytesIO()
    pd.DataFrame(
        [
            {"producto": "A", "monto": 1, "categoria": "X", "fecha": "2026-01-01"},
            {"producto": "B", "monto": 2, "categoria": "X", "fecha": "2026-01-02"},
        ]
    ).to_excel(output, index=False)

    response = _upload(client, auth_headers, output.getvalue(), "ventas.xlsx")

    assert response.status_code == 413


def test_xlsx_with_excessive_declared_size_is_rejected(client, auth_headers, monkeypatch):
    monkeypatch.setattr(etl_routes, "MAX_XLSX_UNCOMPRESSED_BYTES", 100)
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("xl/worksheets/sheet1.xml", b"0" * 1000)

    response = _upload(client, auth_headers, output.getvalue(), "ventas.xlsx")

    assert response.status_code == 413


def test_unreadable_xlsx_returns_fixed_message(client, auth_headers):
    response = _upload(client, auth_headers, b"esto no es un zip", "ventas.xlsx")

    assert response.status_code == 400
    assert response.json()["detail"] == "No se pudo leer el archivo."


def test_upload_does_not_block_other_requests(client, auth_headers, monkeypatch):
    parsing = threading.Event()
    release = threading.Event()
    released_in_time = []

    def slow_parse(_contents):
        parsing.set()
        released_in_time.append(release.wait(timeout=5))
        return []

    monkeypatch.setattr(etl_routes, "_parse_csv", slow_parse)
    upload = threading.Thread(target=_upload, args=(client, auth_headers, HEADER))
    upload.start()
    assert parsing.wait(timeout=5)

    health = client.get("/health")
    release.set()
    upload.join(timeout=10)

    assert health.status_code == 200
    assert released_in_time == [True]


def test_sql_respects_quotes_columns_and_quantity(client, auth_headers, test_db):
    contents = (
        b"INSERT INTO ventas (fecha, categoria, cantidad, monto, producto) VALUES "
        b"('2026-01-02', 'Abarrotes', 3, 12.50, 'Galletas, surtidas'),"
        b"('2026-01-03', 'Abarrotes', 1, 5, 'Te ''verde''');"
    )

    response = _upload(client, auth_headers, contents, "ventas.sql")

    assert response.status_code == 200
    assert response.json()["registros_cargados"] == 2
    first, second = _sales(test_db)
    assert first.producto == "Galletas, surtidas"
    assert float(first.cantidad) == 3.0
    assert second.producto == "Te 'verde'"


def test_sql_without_column_list_uses_default_order(client, auth_headers, test_db):
    contents = b"INSERT INTO ventas VALUES ('Arroz', 10, 'Abarrotes', '2026-01-02');"

    response = _upload(client, auth_headers, contents, "ventas.sql")

    assert response.json()["registros_cargados"] == 1
    assert _sales(test_db)[0].producto == "Arroz"


def test_sql_row_without_date_is_rejected_and_numbered_from_one(client, auth_headers):
    contents = b"INSERT INTO ventas VALUES ('Arroz', 10, 'Abarrotes');"

    response = _upload(client, auth_headers, contents, "ventas.sql")

    body = response.json()
    assert body["registros_cargados"] == 0
    assert body["errores"] == [{"fila": 1, "error": "la fecha es obligatoria"}]


def _second_user_headers(client):
    credentials = {
        "nombre_usuario": "otro_usuario",
        "correo_electronico": "otro@example.com",
        "password": "StrongPass1",
    }
    assert client.post("/users/register", json=credentials).status_code == 201
    login = client.post(
        "/users/login",
        data={"username": credentials["correo_electronico"], "password": credentials["password"]},
    )
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def test_identical_file_is_rejected_for_the_same_user_only(client, auth_headers, test_db):
    contents = HEADER + b"Arroz,10,Abarrotes,2026-01-01\n"

    assert _upload(client, auth_headers, contents).status_code == 200
    assert _upload(client, auth_headers, contents).status_code == 409
    assert len(_sales(test_db)) == 1

    assert _upload(client, _second_user_headers(client), contents).status_code == 200


def test_file_can_be_loaded_again_after_purge(client, auth_headers):
    contents = HEADER + b"Arroz,10,Abarrotes,2026-01-01\n"
    assert _upload(client, auth_headers, contents).status_code == 200

    assert client.delete("/etl/clear-history", headers=auth_headers).status_code == 200

    assert _upload(client, auth_headers, contents).status_code == 200


def test_file_with_no_valid_rows_can_be_fixed_and_retried(client, auth_headers):
    contents = HEADER + b"Arroz,no-numero,Abarrotes,2026-01-01\n"

    assert _upload(client, auth_headers, contents).status_code == 200
    assert _upload(client, auth_headers, contents).status_code == 200
