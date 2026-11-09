"""Tests for ETL (data ingestion) endpoints."""

import io
import json
from datetime import date

import pandas as pd
import pytest

from app.models import models
from app.services import etl_service


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


def test_upload_quantity_defaults_to_one_for_legacy_csv(client, auth_headers, test_db):
    response = client.post(
        "/etl/upload-ventas",
        headers=auth_headers,
        files={
            "file": (
                "ventas.csv",
                b"producto,monto,categoria,fecha\nArroz,10,Abarrotes,2026-03-01",
                "text/csv",
            )
        },
    )

    assert response.status_code == 200
    session = test_db()
    try:
        sale = session.query(models.Venta).one()
        assert float(sale.cantidad) == 1.0
    finally:
        session.close()


def test_upload_quantity_accepts_non_negative_value(client, auth_headers, test_db):
    response = client.post(
        "/etl/upload-ventas",
        headers=auth_headers,
        files={
            "file": (
                "ventas.csv",
                b"producto,monto,cantidad,categoria,fecha\nArroz,10,3,Abarrotes,2026-03-01",
                "text/csv",
            )
        },
    )

    assert response.status_code == 200
    session = test_db()
    try:
        sale = session.query(models.Venta).one()
        assert float(sale.cantidad) == 3.0
    finally:
        session.close()


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


def test_clear_history_deletes_only_current_user_sales(client, auth_headers, second_user, test_db):
    for headers, contents in (
        (auth_headers, b"producto,monto,categoria,fecha\nArroz,10,Abarrotes,2026-01-01"),
        (second_user, b"producto,monto,categoria,fecha\nLeche,5,Lacteos,2026-01-02\nPan,3,Abarrotes,2026-01-03"),
    ):
        upload = client.post(
            "/etl/upload-ventas",
            headers=headers,
            files={"file": ("ventas.csv", contents, "text/csv")},
        )
        assert upload.status_code == 200

    response = client.delete("/etl/clear-history", headers=auth_headers)

    assert response.status_code == 200
    assert "1 registros" in response.json()["message"]
    with test_db() as session:
        remaining = sorted(sale.producto for sale in session.query(models.Venta))
    assert remaining == ["Leche", "Pan"]
    assert client.get("/analytics/ventas", headers=second_user).json()["total_registros"] == 2


def test_clear_history_empty_returns_success_message(client, auth_headers):
    response = client.delete("/etl/clear-history", headers=auth_headers)

    assert response.status_code == 200
    assert "vacio" in response.json()["message"]


# --- Column mapping (task 035) ---------------------------------------------

def _xlsx(records, columns=None):
    output = io.BytesIO()
    pd.DataFrame(records, columns=columns).to_excel(output, index=False)
    return output.getvalue()


def _load(test_db, extension, contents, mapeo=None, user_id=1):
    session = test_db()
    try:
        result = etl_service.load_sales(session, user_id, extension, contents, "hash", mapeo)
        sales = [
            (sale.producto, sale.categoria, float(sale.monto), float(sale.cantidad), sale.fecha_venta)
            for sale in session.query(models.Venta).order_by(models.Venta.id_venta)
        ]
        return result, sales
    finally:
        session.close()


def test_mapped_csv_with_semicolons_loads_every_row(test_db, user_credentials):
    contents = (
        b"Item;Rubro;Total;Unidades;Fecha de venta\n"
        b"Pan;Abarrotes;10.50;2;2026-01-05\n"
        b"Leche;Lacteos;8;1;2026-01-06\n"
        b"Jabon;Limpieza;4.25;3;2026-01-07\n"
    )
    mapeo = {
        "producto": "item",
        "categoria": "rubro",
        "monto": "total",
        "cantidad": "unidades",
        "fecha": "fecha_de_venta",
    }

    result, sales = _load(test_db, "csv", contents, mapeo)

    assert result["registros_cargados"] == 3
    assert sales == [
        ("Pan", "Abarrotes", 10.5, 2.0, date(2026, 1, 5)),
        ("Leche", "Lácteos", 8.0, 1.0, date(2026, 1, 6)),
        ("Jabon", "Limpieza", 4.25, 3.0, date(2026, 1, 7)),
    ]


def test_amount_is_derived_from_unit_price_and_quantity(test_db, user_credentials):
    contents = _xlsx(
        [
            {"Producto": "Pan", "Precio Unit.": 0.333, "Cant.": 3, "Fecha": "2026-01-05"},
            {"Producto": "Sal", "Precio Unit.": 2.5, "Cant.": None, "Fecha": "2026-01-06"},
            {"Producto": "Te", "Precio Unit.": 4, "Cant.": 0, "Fecha": "2026-01-07"},
        ]
    )
    mapeo = {"producto": "producto", "precio_unitario": "precio_unit.", "cantidad": "cant.", "fecha": "fecha"}

    result, sales = _load(test_db, "xlsx", contents, mapeo)

    assert [(name, amount) for name, _, amount, _, _ in sales] == [("Pan", 1.0), ("Sal", 2.5)]
    assert result["errores"] == [
        {"fila": 4, "error": "el precio unitario por la cantidad debe ser mayor que cero"}
    ]


def test_mapped_amount_wins_over_unit_price(test_db, user_credentials):
    contents = b"producto,total,precio,fecha\nPan,10,99,2026-01-05\n"
    mapeo = {"producto": "producto", "monto": "total", "precio_unitario": "precio", "fecha": "fecha"}

    _, sales = _load(test_db, "csv", contents, mapeo)

    assert sales[0][2] == 10.0


def test_unassigned_column_with_a_role_name_does_not_leak(test_db, user_credentials):
    contents = b"producto,categoria,monto,fecha\nPan,Abarrotes,10,2026-01-05\n"
    mapeo = {"producto": "producto", "monto": "monto", "fecha": "fecha"}

    _, sales = _load(test_db, "csv", contents, mapeo)

    assert sales[0][1] == "General"


@pytest.mark.parametrize("fecha", [15, "15", "20260105"])
def test_numeric_dates_are_rejected(test_db, user_credentials, fecha):
    contents = _xlsx([{"producto": "Pan", "monto": 10, "fecha": fecha}])

    result, sales = _load(test_db, "xlsx", contents)

    assert sales == []
    assert result["errores"] == [{"fila": 2, "error": "la fecha no es valida"}]


def test_empty_xlsx_category_is_stored_as_general(test_db, user_credentials):
    contents = _xlsx(
        [
            {"producto": "Pan", "monto": 10, "categoria": None, "fecha": "2026-01-05"},
            {"producto": "Sal", "monto": 5, "categoria": "Abarrotes", "fecha": "2026-01-06"},
        ]
    )

    _, sales = _load(test_db, "xlsx", contents)

    assert [category for _, category, _, _, _ in sales] == ["General", "Abarrotes"]


def test_xlsx_with_headers_and_no_rows_loads_nothing(test_db, user_credentials):
    contents = _xlsx([], columns=["producto", "monto", "categoria", "fecha"])

    result, sales = _load(test_db, "xlsx", contents)

    assert result["registros_leidos"] == 0
    assert sales == []


def test_sql_headers_merge_declared_lists_in_order():
    contents = (
        b"INSERT INTO ventas (producto, monto, fecha) VALUES ('Pan', 10, '2026-01-05');"
        b"INSERT INTO ventas (fecha, total, cantidad) VALUES ('2026-01-06', 5, 2);"
    )

    headers, rows = etl_service.read_table("sql", contents)

    assert headers == ["producto", "monto", "fecha", "total", "cantidad"]
    assert rows[1] == {"fecha": "2026-01-06", "total": "5", "cantidad": "2"}


def _analyze(client, headers, name, contents):
    return client.post(
        "/etl/analizar-columnas",
        headers=headers,
        files={"file": (name, contents, "application/octet-stream")},
    )


def _count(test_db, model):
    with test_db() as session:
        return session.query(model).count()


def test_analyze_csv_proposes_and_samples(client, auth_headers, test_db):
    contents = b"Item;Rubro;Total;Fecha de venta\nPan;Abarrotes;10.50;2026-01-05\nSal;;3;2026-01-06\n"

    response = _analyze(client, auth_headers, "ventas.csv", contents)

    assert response.status_code == 200
    body = response.json()
    assert body["columnas"] == ["item", "rubro", "total", "fecha_de_venta"]
    assert body["muestra"][1] == {"item": "Sal", "rubro": None, "total": "3", "fecha_de_venta": "2026-01-06"}
    assert body["propuesta"]["monto"] == {"columna": "total", "origen": "sinonimo", "candidatos": []}
    assert body["propuesta"]["precio_unitario"] == {"columna": None, "origen": None, "candidatos": []}
    assert body["faltantes"] == []
    assert _count(test_db, models.Venta) == 0
    assert _count(test_db, models.CargaArchivo) == 0


def test_analyze_xlsx_renders_dates_and_whole_numbers(client, auth_headers):
    contents = _xlsx([{"Producto": "Pan", "Cant.": 3.0, "Fecha": pd.Timestamp("2026-01-05")}])

    body = _analyze(client, auth_headers, "ventas.xlsx", contents).json()

    assert body["muestra"] == [{"producto": "Pan", "cant.": "3", "fecha": "2026-01-05"}]
    assert body["faltantes"] == ["monto"]


@pytest.mark.parametrize(
    ("contents", "columnas"),
    [
        (b"INSERT INTO ventas VALUES ('Pan', 10, 'Abarrotes', '2026-01-05', 1);",
         ["producto", "monto", "categoria", "fecha", "cantidad"]),
        (b"INSERT INTO ventas (item, total, dia) VALUES ('Pan', 10, '2026-01-05');",
         ["item", "total", "dia"]),
    ],
)
def test_analyze_sql_with_and_without_column_list(client, auth_headers, contents, columnas):
    body = _analyze(client, auth_headers, "ventas.sql", contents).json()

    assert body["columnas"] == columnas


def test_analyze_sql_without_list_is_exact_in_default_roles(client, auth_headers):
    contents = b"INSERT INTO ventas VALUES ('Pan', 10, 'Abarrotes', '2026-01-05', 1);"

    proposal = _analyze(client, auth_headers, "ventas.sql", contents).json()["propuesta"]

    assert {role: entry["origen"] for role, entry in proposal.items()} == {
        "producto": "exacto",
        "categoria": "exacto",
        "monto": "exacto",
        "precio_unitario": None,
        "cantidad": "exacto",
        "fecha": "exacto",
    }


def test_analyze_requires_authentication(client):
    assert _analyze(client, {}, "ventas.csv", b"producto\nPan\n").status_code == 401


def _upload_mapped(client, headers, contents, mapeo, name="ventas.csv"):
    return client.post(
        "/etl/upload-ventas",
        headers=headers,
        files={"file": (name, contents, "text/csv")},
        data={"mapeo": mapeo},
    )


def test_upload_with_mapping_loads_renamed_columns(client, auth_headers):
    contents = b"Item,Total,Fecha\nPan,10,2026-01-05\n"
    mapeo = json.dumps({"producto": "item", "monto": "total", "fecha": "fecha"})

    response = _upload_mapped(client, auth_headers, contents, mapeo)

    assert response.status_code == 200
    assert response.json()["registros_cargados"] == 1


def test_upload_rejects_malformed_mapping_json(client, auth_headers):
    response = _upload_mapped(client, auth_headers, b"producto,monto,fecha\n", "{no es json")

    assert response.status_code == 400
    assert response.json()["detail"] == "El mapeo de columnas no es un JSON válido."


def test_upload_rejects_invalid_mapping_without_file_prefix(client, auth_headers):
    mapeo = json.dumps({"producto": "item", "monto": "total"})

    response = _upload_mapped(client, auth_headers, b"item,total\nPan,10\n", mapeo)

    assert response.status_code == 400
    assert response.json()["detail"] == "Falta asignar: Fecha."


def test_duplicate_file_answers_409_before_validating_the_mapping(client, auth_headers):
    contents = b"producto,monto,fecha\nPan,10,2026-01-05\n"
    assert _upload_mapped(client, auth_headers, contents, json.dumps(
        {"producto": "producto", "monto": "monto", "fecha": "fecha"})).status_code == 200

    response = _upload_mapped(client, auth_headers, contents, json.dumps({"producto": "nada"}))

    assert response.status_code == 409


def test_upload_without_mapping_still_requires_exact_names(client, auth_headers):
    response = client.post(
        "/etl/upload-ventas",
        headers=auth_headers,
        files={"file": ("ventas.csv", b"item,total,fecha\nPan,10,2026-01-05\n", "text/csv")},
    )

    assert response.status_code == 400
    assert "columnas requeridas" in response.json()["detail"]
