"""Tests for product names: normalization, /analytics/productos, and product filters."""

from datetime import date

import pytest

from app.models import models
from app.services.category_service import normalize_product
from tests.test_forecast_api import _months, _upload

NEEDS_CATEGORY = "Para filtrar por producto, elige también su categoría."


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("coca  cola", "Coca Cola"),
        ("  COCA COLA ", "Coca Cola"),
        ("café molido", "Café Molido"),
        ("Hershey's", "Hershey's"),
        ("7up", "7up"),
    ],
)
def test_normalize_product_unifies_spaces_and_case_and_keeps_accents(raw, expected):
    assert normalize_product(raw) == expected


def test_upload_stores_the_normalized_product_name(client, auth_headers, test_db):
    _upload(client, auth_headers, [("coca  COLA", 10, "Bebidas", date(2024, 1, 5), 1)])

    session = test_db()
    try:
        assert [venta.producto for venta in session.query(models.Venta)] == ["Coca Cola"]
    finally:
        session.close()


# ---------------------------------------------------------------- GET /productos


def test_products_of_a_category_are_sorted_and_merge_spellings(client, auth_headers):
    _upload(
        client,
        auth_headers,
        [
            ("sprite", 10, "Bebidas", date(2024, 1, 5), 1),
            ("Coca Cola", 10, "Bebidas", date(2024, 1, 6), 1),
            ("coca cola", 10, "bebidas", date(2024, 1, 7), 1),
            ("Arroz", 10, "Abarrotes", date(2024, 1, 8), 1),
        ],
    )

    response = client.get("/analytics/productos", headers=auth_headers, params={"categoria": "BEBIDAS"})

    assert response.status_code == 200
    assert response.json()["categoria"] == "Bebidas"
    assert response.json()["productos"] == ["Coca Cola", "Sprite"]


def test_products_require_a_category(client, auth_headers):
    assert client.get("/analytics/productos", headers=auth_headers).status_code == 422


def test_products_of_an_unknown_category_are_empty(client, auth_headers):
    _upload(client, auth_headers, [("Arroz", 10, "Abarrotes", date(2024, 1, 8), 1)])

    body = client.get("/analytics/productos", headers=auth_headers, params={"categoria": "ropa"}).json()

    assert body["productos"] == []


def test_products_are_isolated_between_users(client, auth_headers, second_user):
    _upload(client, auth_headers, [("Coca Cola", 10, "Bebidas", date(2024, 1, 5), 1)])
    _upload(client, second_user, [("Sprite", 10, "Bebidas", date(2024, 1, 5), 1)])

    body = client.get("/analytics/productos", headers=second_user, params={"categoria": "Bebidas"}).json()

    assert body["productos"] == ["Sprite"]


# ---------------------------------------------------------------- product filters


@pytest.mark.parametrize(
    ("method", "path"),
    [("GET", "/analytics/forecast"), ("GET", "/analytics/ventas"), ("POST", "/analytics/predicciones")],
)
def test_a_product_without_its_category_is_unprocessable(client, auth_headers, method, path):
    if method == "POST":
        response = client.post(path, headers=auth_headers, json={"producto": "Arroz"})
        assert response.status_code == 422
        assert NEEDS_CATEGORY in response.text
    else:
        response = client.get(path, headers=auth_headers, params={"producto": "Arroz"})
        assert response.status_code == 422
        assert response.json()["detail"] == NEEDS_CATEGORY


def test_forecast_for_a_product_uses_only_its_sales(client, auth_headers):
    _upload(client, auth_headers, _months(12))

    params = {"categoria": "abarrotes", "producto": "ARROZ"}
    body = client.get("/analytics/forecast", headers=auth_headers, params=params).json()
    category = client.get("/analytics/forecast", headers=auth_headers, params={"categoria": "abarrotes"}).json()

    assert body["categoria"] == "Abarrotes"
    assert body["producto"] == "Arroz"
    assert body["historial"][0]["monto"] == 1000
    assert body["historial"][0]["cantidad"] == 3
    assert category["historial"][0]["monto"] == 1050
    assert category["producto"] is None


def test_forecast_for_a_product_in_another_category_is_unprocessable(client, auth_headers):
    _upload(client, auth_headers, _months(12))

    params = {"categoria": "Lácteos", "producto": "Arroz"}
    response = client.get("/analytics/forecast", headers=auth_headers, params=params)

    assert response.status_code == 422
    assert response.json()["detail"] == (
        "No hay ventas del producto 'Arroz' en la categoría 'Lácteos' para proyectar."
    )


def test_forecast_for_a_product_with_short_history_is_unprocessable(client, auth_headers):
    rows = _months(12) + [("Avena", 30, "Abarrotes", date(2024, 11, 3), 1)]
    _upload(client, auth_headers, rows)

    params = {"categoria": "Abarrotes", "producto": "Avena"}
    response = client.get("/analytics/forecast", headers=auth_headers, params=params)

    assert response.status_code == 422
    assert "6 meses" in response.json()["detail"]


def test_saving_a_product_projection_stores_the_product(client, auth_headers, test_db):
    _upload(client, auth_headers, _months(12))

    payload = {"categoria": "abarrotes", "producto": "arroz"}
    batch = client.post("/analytics/predicciones", headers=auth_headers, json=payload).json()
    listed = client.get("/analytics/predicciones", headers=auth_headers).json()["lotes"][0]

    assert batch["categoria"] == "Abarrotes"
    assert batch["producto"] == "Arroz"
    assert listed["producto"] == "Arroz"
    session = test_db()
    try:
        rows = session.query(models.Prediccion).all()
        assert {(row.producto, row.producto_referencia) for row in rows} == {("Arroz", "Arroz")}
    finally:
        session.close()


def test_saving_a_category_projection_keeps_the_product_empty(client, auth_headers):
    _upload(client, auth_headers, _months(12))

    batch = client.post("/analytics/predicciones", headers=auth_headers, json={"categoria": "Abarrotes"}).json()

    assert batch["producto"] is None


def test_sales_history_filters_by_product_within_its_category(client, auth_headers):
    _upload(client, auth_headers, _months(6))

    params = {"categoria": "abarrotes", "producto": "sal", "limit": 4}
    body = client.get("/analytics/ventas", headers=auth_headers, params=params).json()

    assert body["total_registros"] == 6
    assert body["total_paginas"] == 2
    assert {row["producto"] for row in body["registros"]} == {"Sal"}
    assert len(body["registros"]) == 4
