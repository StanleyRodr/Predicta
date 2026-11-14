"""Tests for /analytics/stats/series and the filters of /analytics/ventas."""

from datetime import date

import pytest

from app.models import models
from tests.conftest import register_verified


def _upload(client, headers, rows):
    lines = ["producto,monto,categoria,fecha,cantidad"]
    lines.extend(",".join(map(str, row)) for row in rows)
    response = client.post(
        "/etl/upload-ventas",
        headers=headers,
        files={"file": ("ventas.csv", "\n".join(lines).encode(), "text/csv")},
    )
    assert response.status_code == 200, response.text


def _other_headers(client):
    user = {
        "nombre_usuario": "otro",
        "correo_electronico": "otro@example.com",
        "password": "StrongPass1",
    }
    register_verified(client, user)
    token = client.post(
        "/users/login",
        data={"username": user["correo_electronico"], "password": user["password"]},
    ).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


SALES = [
    ("Arroz", 100, "Abarrotes", "2025-01-05", 2),
    ("Leche", 50, "Lácteos", "2025-01-05", 1),
    ("Arroz", 30, "Abarrotes", "2025-01-20", 1),
    ("Yogur", 20.5, "Lácteos", "2025-03-02", 3),
    ("Leche", 70, "Lácteos", "2026-01-10", 4),
]


def _series(client, headers, **params):
    response = client.get("/analytics/stats/series", headers=headers, params=params)
    assert response.status_code == 200, response.text
    return response.json()


def test_monthly_series_groups_by_year_and_month_without_empty_months(
    client, auth_headers
):
    _upload(client, auth_headers, SALES)

    body = _series(client, auth_headers)

    assert body["granularidad"] == "mes"
    assert body["categoria"] is None
    assert body["puntos"] == [
        {
            "periodo": "2025-01",
            "anio": 2025,
            "mes": 1,
            "dia": None,
            "categoria": None,
            "ingresos": 180.0,
            "cantidad": 4.0,
            "ventas_realizadas": 3,
        },
        {
            "periodo": "2025-03",
            "anio": 2025,
            "mes": 3,
            "dia": None,
            "categoria": None,
            "ingresos": 20.5,
            "cantidad": 3.0,
            "ventas_realizadas": 1,
        },
        {
            "periodo": "2026-01",
            "anio": 2026,
            "mes": 1,
            "dia": None,
            "categoria": None,
            "ingresos": 70.0,
            "cantidad": 4.0,
            "ventas_realizadas": 1,
        },
    ]


def test_monthly_series_total_matches_global_stats_in_the_same_range(
    client, auth_headers
):
    _upload(client, auth_headers, SALES)
    params = {"fecha_desde": "2025-01-06", "fecha_hasta": "2025-12-31"}

    points = _series(client, auth_headers, **params)["puntos"]
    stats = client.get("/analytics/stats", headers=auth_headers, params=params).json()

    assert sum(point["ingresos"] for point in points) == pytest.approx(
        stats["metricas_globales"]["total_ingresos"]
    )
    assert sum(point["ventas_realizadas"] for point in points) == stats[
        "metricas_globales"
    ]["cantidad_operaciones"]


def test_daily_series_lists_observed_days_of_one_month(client, auth_headers):
    _upload(client, auth_headers, SALES)

    body = _series(
        client,
        auth_headers,
        granularidad="dia",
        fecha_desde="2025-01-01",
        fecha_hasta="2025-01-31",
    )

    assert [(p["periodo"], p["dia"], p["ingresos"]) for p in body["puntos"]] == [
        ("2025-01-05", 5, 150.0),
        ("2025-01-20", 20, 30.0),
    ]
    assert all(p["anio"] == 2025 and p["mes"] == 1 for p in body["puntos"])


@pytest.mark.parametrize("value", ["lacteos", "Lácteos", "  LACTEOS "])
def test_category_filter_ignores_case_and_accents(client, auth_headers, value):
    _upload(client, auth_headers, SALES)

    body = _series(client, auth_headers, categoria=value)

    assert body["categoria"] == "Lácteos"
    assert [(p["periodo"], p["ingresos"]) for p in body["puntos"]] == [
        ("2025-01", 50.0),
        ("2025-03", 20.5),
        ("2026-01", 70.0),
    ]


def test_category_filter_matches_user_defined_category_without_accents(
    client, auth_headers
):
    _upload(client, auth_headers, [("Radio", 80, "Electrónica", "2025-02-01", 1)])

    body = _series(client, auth_headers, categoria="electronica")

    assert body["categoria"] == "Electrónica"
    assert [p["ingresos"] for p in body["puntos"]] == [80.0]


def test_category_filter_includes_legacy_spellings_of_the_same_category(
    client, auth_headers, test_db
):
    _upload(client, auth_headers, SALES)
    session = test_db()
    try:
        owner = session.query(models.Usuario).one()
        session.add(
            models.Venta(
                id_usuario=owner.id_usuario,
                producto="Queso",
                monto=10,
                cantidad=1,
                categoria="lacteos",
                fecha_venta=date(2025, 3, 15),
            )
        )
        session.commit()
    finally:
        session.close()

    body = _series(client, auth_headers, categoria="Lácteos", fecha_desde="2025-03-01")

    assert [(p["periodo"], p["ingresos"]) for p in body["puntos"]] == [
        ("2025-03", 30.5),
        ("2026-01", 70.0),
    ]


def test_unknown_category_returns_empty_series(client, auth_headers):
    _upload(client, auth_headers, SALES)

    body = _series(client, auth_headers, categoria="ropa")

    assert body["categoria"] == "Ropa"
    assert body["puntos"] == []


def test_series_by_category_returns_one_point_per_month_and_category(
    client, auth_headers
):
    _upload(client, auth_headers, SALES)

    body = _series(client, auth_headers, por_categoria=True, fecha_hasta="2025-12-31")

    assert body["por_categoria"] is True
    assert [(p["periodo"], p["categoria"], p["ingresos"]) for p in body["puntos"]] == [
        ("2025-01", "Abarrotes", 130.0),
        ("2025-01", "Lácteos", 50.0),
        ("2025-03", "Lácteos", 20.5),
    ]


@pytest.mark.parametrize(
    "params",
    [
        {"granularidad": "semana"},
        {"fecha_desde": "2025-02-01", "fecha_hasta": "2025-01-01"},
    ],
)
def test_series_rejects_invalid_input(client, auth_headers, params):
    response = client.get("/analytics/stats/series", headers=auth_headers, params=params)

    assert response.status_code == 422


def test_series_never_includes_other_users_sales(client, auth_headers):
    _upload(client, auth_headers, SALES)
    other = _other_headers(client)
    _upload(client, other, [("Ajeno", 999, "Lácteos", "2025-01-05", 9)])

    mine = _series(client, auth_headers, categoria="lacteos", fecha_hasta="2025-01-31")
    theirs = _series(client, other)

    assert [p["ingresos"] for p in mine["puntos"]] == [50.0]
    assert [p["ingresos"] for p in theirs["puntos"]] == [999.0]


def test_series_requires_authentication(client):
    assert client.get("/analytics/stats/series").status_code == 401


def test_sales_page_filters_by_date_range_and_category(client, auth_headers):
    _upload(client, auth_headers, SALES)
    _upload(client, _other_headers(client), [("Ajeno", 999, "Lácteos", "2025-01-05", 9)])

    response = client.get(
        "/analytics/ventas",
        headers=auth_headers,
        params={
            "categoria": "lacteos",
            "fecha_desde": "2025-01-01",
            "fecha_hasta": "2025-12-31",
            "limit": 1,
            "skip": 1,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total_registros"] == 2
    assert body["total_paginas"] == 2
    assert body["pagina_actual"] == 2
    assert [(r["producto"], r["fecha"]) for r in body["registros"]] == [
        ("Leche", "2025-01-05 00:00:00")
    ]


def test_sales_page_rejects_inverted_range(client, auth_headers):
    response = client.get(
        "/analytics/ventas",
        headers=auth_headers,
        params={"fecha_desde": "2025-02-01", "fecha_hasta": "2025-01-01"},
    )

    assert response.status_code == 422


def test_openapi_documents_series_and_sales_responses(client):
    paths = client.get("/openapi.json").json()["paths"]

    for path in ("/analytics/stats/series", "/analytics/ventas"):
        schema = paths[path]["get"]["responses"]["200"]["content"]["application/json"]["schema"]
        assert "$ref" in schema
