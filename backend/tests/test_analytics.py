"""Tests for analytics and prediction endpoints."""

def _upload_sales(client, headers, rows):
    csv_rows = ["producto,monto,categoria,fecha"]
    csv_rows.extend(",".join(map(str, row)) for row in rows)
    return client.post(
        "/etl/upload-ventas",
        headers=headers,
        files={"file": ("ventas.csv", "\n".join(csv_rows).encode(), "text/csv")},
    )


def test_stats_without_data_returns_zeros(client, auth_headers):
    response = client.get("/analytics/stats", headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["metricas_globales"] == {
        "total_ingresos": 0.0,
        "cantidad_operaciones": 0,
        "ticket_promedio": 0.0,
        "venta_mas_alta": 0.0,
    }


def test_stats_with_data_returns_aggregates(client, auth_headers):
    assert _upload_sales(
        client,
        auth_headers,
        [
            ("Arroz", 10, "Abarrotes", "2026-01-01"),
            ("Leche", 20, "Lacteos", "2026-01-02"),
        ],
    ).status_code == 200

    response = client.get("/analytics/stats", headers=auth_headers)
    metrics = response.json()["metricas_globales"]

    assert response.status_code == 200
    assert metrics["total_ingresos"] == 30.0
    assert metrics["cantidad_operaciones"] == 2
    assert metrics["ticket_promedio"] == 15.0
    assert metrics["venta_mas_alta"] == 20.0


def test_category_breakdown_groups_sales(client, auth_headers):
    assert _upload_sales(
        client,
        auth_headers,
        [
            ("Arroz", 10, "Abarrotes", "2026-01-01"),
            ("Frijol", 30, "Abarrotes", "2026-01-02"),
            ("Leche", 20, "Lacteos", "2026-01-02"),
        ],
    ).status_code == 200

    response = client.get("/analytics/stats/categories", headers=auth_headers)
    categories = {item["categoria"]: item for item in response.json()["analisis_por_categoria"]}

    assert response.status_code == 200
    assert categories["Abarrotes"]["ingresos_totales"] == 40.0
    assert categories["Abarrotes"]["cantidad_ventas"] == 2
    assert categories["Abarrotes"]["ticket_promedio"] == 20.0


def test_temporal_evolution_is_sorted(client, auth_headers):
    assert _upload_sales(
        client,
        auth_headers,
        [
            ("Arroz", 20, "Abarrotes", "2026-01-03"),
            ("Arroz", 10, "Abarrotes", "2026-01-01"),
        ],
    ).status_code == 200

    response = client.get("/analytics/stats/temporal", headers=auth_headers)
    evolution = response.json()["evolucion_diaria"]

    assert response.status_code == 200
    assert [item["fecha"] for item in evolution] == ["2026-01-01", "2026-01-03"]


def test_predict_with_insufficient_data_returns_error(client, auth_headers):
    assert _upload_sales(
        client, auth_headers, [("Arroz", 20, "Abarrotes", "2026-01-01")]
    ).status_code == 200

    response = client.get("/analytics/predict", headers=auth_headers)

    assert response.status_code == 200
    assert "error" in response.json()


def test_predict_with_two_days_returns_forecast(client, auth_headers):
    assert _upload_sales(
        client,
        auth_headers,
        [
            ("Arroz", 20, "Abarrotes", "2026-01-01"),
            ("Arroz", 30, "Abarrotes", "2026-01-02"),
        ],
    ).status_code == 200

    response = client.get("/analytics/predict", headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["proxima_fecha"] == "2026-01-03"
    assert response.json()["monto_predicho"] >= 0


def test_export_excel_returns_xlsx(client, auth_headers):
    assert _upload_sales(
        client, auth_headers, [("Arroz", 20, "Abarrotes", "2026-01-01")]
    ).status_code == 200

    response = client.get("/analytics/export/excel", headers=auth_headers)

    assert response.status_code == 200
    assert response.headers["content-type"].startswith(
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    assert response.content[:2] == b"PK"


def test_export_pdf_returns_pdf(client, auth_headers):
    assert _upload_sales(
        client, auth_headers, [("Arroz", 20, "Abarrotes", "2026-01-01")]
    ).status_code == 200

    response = client.get("/analytics/export/pdf", headers=auth_headers)

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content.startswith(b"%PDF")


def test_annual_report_requires_multiple_months(client, auth_headers):
    assert _upload_sales(
        client, auth_headers, [("Arroz", 20, "Abarrotes", "2026-01-01")]
    ).status_code == 200

    response = client.get(
        "/analytics/reporte-predictivo-anual-pdf", headers=auth_headers
    )

    assert response.status_code == 400
    assert "Muestreo insuficiente" in response.json()["detail"]
