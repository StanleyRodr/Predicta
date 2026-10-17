"""Tests for ETL (data ingestion) endpoints."""

import io

import pandas as pd


def test_upload_csv_returns_success(client, auth_headers):
    contents = (
        b"producto,monto,categoria,fecha\n"
        b"Arroz,25.50,Abarrotes,2026-01-10\n"
        b"Leche,18.00,Lacteos,2026-01-11\n"
    )

    response = client.post(
        "/etl/upload-ventas",
        headers=auth_headers,
        files={"file": ("ventas.csv", contents, "text/csv")},
    )

    assert response.status_code == 200
    assert "2 registros" in response.json()["message"]


def test_upload_excel_returns_success(client, auth_headers):
    output = io.BytesIO()
    pd.DataFrame(
        [
            {"producto": "Jabon", "monto": 12.5, "categoria": "Limpieza", "fecha": "2026-02-01"}
        ]
    ).to_excel(output, index=False)

    response = client.post(
        "/etl/upload-ventas",
        headers=auth_headers,
        files={
            "file": (
                "ventas.xlsx",
                output.getvalue(),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )

    assert response.status_code == 200
    assert "1 registros" in response.json()["message"]


def test_upload_csv_detects_semicolon_and_cp1252(client, auth_headers):
    contents = (
        "producto;monto;categoria;fecha\n"
        "Café;25,50;Bebidas;2026-03-01\n"
    ).encode("cp1252")

    response = client.post(
        "/etl/upload-ventas",
        headers=auth_headers,
        files={"file": ("ventas.csv", contents, "text/csv")},
    )

    assert response.status_code == 200
    assert response.json()["registros_cargados"] == 1
    assert response.json()["filas_rechazadas"] == 0


def test_upload_rejects_invalid_rows_without_silent_defaults(client, auth_headers):
    contents = (
        b"producto,monto,categoria,fecha\n"
        b"Arroz,no-numero,Abarrotes,2026-03-01\n"
        b"Leche,18,Lacteos,no-es-fecha\n"
        b"Cafe,12,Bebidas,2026-03-02\n"
    )

    response = client.post(
        "/etl/upload-ventas",
        headers=auth_headers,
        files={"file": ("ventas.csv", contents, "text/csv")},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["registros_leidos"] == 3
    assert body["registros_cargados"] == 1
    assert body["filas_rechazadas"] == 2
    assert len(body["errores"]) == 2


def test_upload_rejects_csv_without_required_columns(client, auth_headers):
    response = client.post(
        "/etl/upload-ventas",
        headers=auth_headers,
        files={"file": ("ventas.csv", b"producto,monto\nArroz,10\n", "text/csv")},
    )

    assert response.status_code == 400
    assert "columnas requeridas" in response.json()["detail"]


def test_upload_invalid_format_returns_bad_request(client, auth_headers):
    response = client.post(
        "/etl/upload-ventas",
        headers=auth_headers,
        files={"file": ("ventas.txt", b"contenido", "text/plain")},
    )

    assert response.status_code == 400


def test_upload_without_token_returns_unauthorized(client):
    response = client.post(
        "/etl/upload-ventas",
        files={"file": ("ventas.csv", b"producto,monto\nArroz,10", "text/csv")},
    )

    assert response.status_code == 401


def test_clear_history_deletes_only_current_user_sales(client, auth_headers):
    upload = client.post(
        "/etl/upload-ventas",
        headers=auth_headers,
        files={
            "file": (
                "ventas.csv",
                b"producto,monto,categoria,fecha\nArroz,10,Abarrotes,2026-01-01",
                "text/csv",
            )
        },
    )
    assert upload.status_code == 200

    response = client.delete("/etl/clear-history", headers=auth_headers)

    assert response.status_code == 200
    assert "1 registros" in response.json()["message"]


def test_clear_history_empty_returns_success_message(client, auth_headers):
    response = client.delete("/etl/clear-history", headers=auth_headers)

    assert response.status_code == 200
    assert "vacio" in response.json()["message"]
