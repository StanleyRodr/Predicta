"""Tests for /analytics/forecast and the saved forecasts in /analytics/predicciones."""

import calendar
from datetime import date

import pytest

from app.models import models


def _upload(client, headers, rows):
    lines = ["producto,monto,categoria,fecha,cantidad"]
    lines.extend(",".join(map(str, row)) for row in rows)
    response = client.post(
        "/etl/upload-ventas",
        headers=headers,
        files={"file": ("ventas.csv", "\n".join(lines).encode(), "text/csv")},
    )
    assert response.status_code == 200, response.text


def _months(count, start=(2024, 1), partial_last=False):
    """Sales in two categories each month; every month ends with a sale on its last day."""
    rows = []
    for index in range(count):
        year = start[0] + (start[1] - 1 + index) // 12
        month = (start[1] - 1 + index) % 12 + 1
        last = calendar.monthrange(year, month)[1]
        rows.append(("Arroz", 1000 + 25 * index, "Abarrotes", date(year, month, 5), 3))
        rows.append(("Leche", 400 + 10 * index, "Lácteos", date(year, month, 12), 5))
        if not (partial_last and index == count - 1):
            rows.append(("Sal", 50, "Abarrotes", date(year, month, last), 1))
    return rows


def _other_headers(client):
    user = {"nombre_usuario": "otra", "correo_electronico": "otra@example.com", "password": "StrongPass1"}
    assert client.post("/users/register", json=user).status_code == 201
    token = client.post(
        "/users/login", data={"username": user["correo_electronico"], "password": user["password"]}
    ).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _count_predictions(test_db):
    session = test_db()
    try:
        return session.query(models.Prediccion).count()
    finally:
        session.close()


# ---------------------------------------------------------------- GET /forecast


def test_forecast_returns_history_projection_and_metrics_without_writing(client, auth_headers, test_db):
    _upload(client, auth_headers, _months(24))

    response = client.get("/analytics/forecast", headers=auth_headers)

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["categoria"] is None
    assert body["modelo"] == "tendencia"
    assert body["horizonte_aplicado"] == 12
    assert body["meses_observados"] == 24
    assert len(body["historial"]) == 24
    assert body["mes_parcial"] is None
    assert [point["periodo"] for point in body["proyeccion"]][:2] == ["2026-01", "2026-02"]
    assert body["proyeccion"][5]["extrapolacion"] is False
    assert body["proyeccion"][6]["extrapolacion"] is True
    for point in body["proyeccion"]:
        for target in ("monto", "cantidad"):
            values = point[target]
            assert 0 <= values["inferior"] <= values["prediccion"] <= values["superior"]
    assert body["metricas"]["monto"]["origenes"] == 6
    assert body["metricas"]["monto"]["referencia"] in {"ultimo_valor", "mismo_mes_anio_anterior", "promedio_movil_3"}
    assert _count_predictions(test_db) == 0


def test_forecast_for_a_category_ignores_accents(client, auth_headers):
    _upload(client, auth_headers, _months(12))

    body = client.get("/analytics/forecast", headers=auth_headers, params={"categoria": "lacteos"}).json()
    total = client.get("/analytics/forecast", headers=auth_headers).json()

    assert body["categoria"] == "Lácteos"
    assert body["historial"][0]["monto"] == 400
    assert body["historial"][0]["monto"] < total["historial"][0]["monto"]


def test_forecast_with_twelve_months_warns_that_seasons_are_not_modeled(client, auth_headers):
    _upload(client, auth_headers, _months(12))

    body = client.get("/analytics/forecast", headers=auth_headers).json()

    assert body["horizonte_aplicado"] == 6
    assert "tendencia" in body["advertencia"]
    assert len(body["advertencias"]) == 1
    assert body["advertencias"][0] == body["advertencia"]


def test_forecast_lists_each_warning_and_keeps_the_joined_text(client, auth_headers):
    _upload(client, auth_headers, _months(24))

    body = client.get("/analytics/forecast", headers=auth_headers).json()

    assert body["horizonte_aplicado"] == 12
    assert len(body["advertencias"]) == 2
    assert "tendencia" in body["advertencias"][0]
    assert "extrapolación" in body["advertencias"][1]
    assert " ".join(body["advertencias"]) == body["advertencia"]


def test_forecast_reports_the_incomplete_last_month_apart(client, auth_headers):
    _upload(client, auth_headers, _months(9, partial_last=True))

    body = client.get("/analytics/forecast", headers=auth_headers).json()

    assert body["meses_observados"] == 8
    assert body["mes_parcial"]["periodo"] == "2024-09"
    assert body["proyeccion"][0]["periodo"] == "2024-09"


def test_forecast_with_five_months_is_unprocessable(client, auth_headers):
    _upload(client, auth_headers, _months(5))

    response = client.get("/analytics/forecast", headers=auth_headers)

    assert response.status_code == 422
    assert response.json()["detail"] == (
        "Se necesitan al menos 6 meses completos de ventas para proyectar; hay 5 y faltan 1."
    )


def test_forecast_for_a_category_without_sales_is_unprocessable(client, auth_headers):
    _upload(client, auth_headers, _months(12))

    response = client.get("/analytics/forecast", headers=auth_headers, params={"categoria": "ropa"})

    assert response.status_code == 422
    assert response.json()["detail"] == "No hay ventas de la categoría 'Ropa' para proyectar."


def test_forecast_without_sales_is_unprocessable(client, auth_headers):
    response = client.get("/analytics/forecast", headers=auth_headers)

    assert response.status_code == 422
    assert response.json()["detail"] == "No hay ventas para proyectar."


# ---------------------------------------------------------------- saved forecasts


def test_saving_stores_one_row_per_projected_month_in_one_batch(client, auth_headers, test_db):
    _upload(client, auth_headers, _months(12))
    shown = client.get("/analytics/forecast", headers=auth_headers).json()

    response = client.post("/analytics/predicciones", headers=auth_headers, json={"categoria": None})

    assert response.status_code == 201, response.text
    batch = response.json()
    assert batch["tipo"] == "mensual"
    assert batch["categoria"] is None
    assert batch["modelo"] == "tendencia"
    assert batch["horizonte"] == 6
    assert len(batch["puntos"]) == 6
    assert batch["puntos"][0]["monto_proyectado"] == shown["proyeccion"][0]["monto"]["prediccion"]
    assert batch["puntos"][0]["cantidad_superior"] == shown["proyeccion"][0]["cantidad"]["superior"]
    assert _count_predictions(test_db) == 6


def test_saving_a_category_keeps_its_display_name(client, auth_headers):
    _upload(client, auth_headers, _months(12))

    batch = client.post("/analytics/predicciones", headers=auth_headers, json={"categoria": "LACTEOS"}).json()

    assert batch["categoria"] == "Lácteos"


def test_saving_without_enough_history_stores_nothing(client, auth_headers, test_db):
    _upload(client, auth_headers, _months(5))

    response = client.post("/analytics/predicciones", headers=auth_headers, json={})

    assert response.status_code == 422
    assert _count_predictions(test_db) == 0


def test_saved_batches_are_paginated_newest_first(client, auth_headers):
    _upload(client, auth_headers, _months(12))
    saved = [
        client.post("/analytics/predicciones", headers=auth_headers, json={"categoria": name}).json()["lote"]
        for name in (None, "Abarrotes", "Lácteos")
    ]

    first = client.get("/analytics/predicciones", headers=auth_headers, params={"limit": 2}).json()
    second = client.get("/analytics/predicciones", headers=auth_headers, params={"limit": 2, "skip": 2}).json()

    assert first["total_lotes"] == 3
    assert first["total_paginas"] == 2
    assert [batch["lote"] for batch in first["lotes"]] == [saved[2], saved[1]]
    assert [batch["lote"] for batch in second["lotes"]] == [saved[0]]
    assert second["pagina_actual"] == 2


def test_saved_batches_are_isolated_between_users(client, auth_headers):
    _upload(client, auth_headers, _months(12))
    client.post("/analytics/predicciones", headers=auth_headers, json={})
    other = _other_headers(client)

    body = client.get("/analytics/predicciones", headers=other).json()

    assert body["total_lotes"] == 0
    assert body["lotes"] == []


def test_legacy_daily_rows_are_listed_as_their_own_batches(client, auth_headers, test_db):
    session = test_db()
    try:
        owner = session.query(models.Usuario).one()
        session.add(
            models.Prediccion(
                id_usuario=owner.id_usuario,
                lote="legado-1",
                tipo="diaria",
                producto_referencia="GLOBAL",
                fecha_proyeccion=date(2026, 11, 1),
                monto_proyectado=8036.56,
                cantidad_proyectada=216.33,
                r2_validacion=0.22,
            )
        )
        session.commit()
    finally:
        session.close()

    batch = client.get("/analytics/predicciones", headers=auth_headers).json()["lotes"][0]

    assert batch["tipo"] == "diaria"
    assert batch["lote"] == "legado-1"
    assert batch["modelo"] is None
    assert batch["puntos"] == [
        {
            "fecha_proyeccion": "2026-11-01",
            "extrapolacion": None,
            "monto_proyectado": 8036.56,
            "monto_inferior": None,
            "monto_superior": None,
            "cantidad_proyectada": 216.33,
            "cantidad_inferior": None,
            "cantidad_superior": None,
        }
    ]


def test_r2_validation_accepts_large_negative_values(client, auth_headers, test_db):
    session = test_db()
    try:
        owner = session.query(models.Usuario).one()
        session.add(
            models.Prediccion(
                id_usuario=owner.id_usuario,
                lote="x",
                tipo="mensual",
                producto_referencia="GLOBAL",
                fecha_proyeccion=date(2026, 1, 31),
                cantidad_proyectada=1,
                r2_validacion=-123456.789,
            )
        )
        session.commit()
        assert session.query(models.Prediccion).one().r2_validacion == pytest.approx(-123456.789)
    finally:
        session.close()


# ---------------------------------------------------------------- contract


def test_every_json_route_documents_its_response(client):
    paths = client.get("/openapi.json").json()["paths"]
    files = {"/analytics/export/excel", "/analytics/export/pdf", "/analytics/reporte-predictivo-anual-pdf"}

    for path, operations in paths.items():
        if not path.startswith(("/analytics", "/etl")) or path in files or "{" in path:
            continue
        for method, operation in operations.items():
            success = next(code for code in operation["responses"] if code.startswith("2"))
            schema = operation["responses"][success]["content"]["application/json"]["schema"]
            assert "$ref" in schema, f"{method.upper()} {path}"
