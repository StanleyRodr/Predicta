"""Characterization tests for the Excel and PDF report endpoints."""

import calendar
import io
import re
from concurrent.futures import ThreadPoolExecutor
from datetime import date

import pandas as pd
import pytest
from openpyxl import load_workbook
from pypdf import PdfReader
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.models import models
from app.services import report_service


def _upload(client, headers, rows):
    lines = ["producto,monto,categoria,fecha"]
    lines.extend(",".join(map(str, row)) for row in rows)
    response = client.post(
        "/etl/upload-ventas",
        headers=headers,
        files={"file": ("ventas.csv", "\n".join(lines).encode(), "text/csv")},
    )
    assert response.status_code == 200, response.text


def _monthly_rows(months, start=(2024, 1), complete=False):
    """Two sales per month; ``complete`` adds one on the last day so no month is partial."""
    rows = []
    for index in range(months):
        year = start[0] + (start[1] - 1 + index) // 12
        month = (start[1] - 1 + index) % 12 + 1
        rows.append(("Arroz", 1000 + 10 * index, "Abarrotes", date(year, month, 10)))
        rows.append(("Jabon", 300 + 5 * index, "Limpieza", date(year, month, 20)))
        if complete:
            last_day = calendar.monthrange(year, month)[1]
            rows.append(("Sal", 50, "Abarrotes", date(year, month, last_day)))
    return rows


def _pdf_text(response):
    assert response.status_code == 200, response.text
    assert response.headers["content-type"] == "application/pdf"
    reader = PdfReader(io.BytesIO(response.content))
    return len(reader.pages), "\n".join(page.extract_text() for page in reader.pages)


def _other_user_headers(client):
    user = {
        "nombre_usuario": "otro",
        "correo_electronico": "otro@example.com",
        "password": "StrongPass1",
    }
    assert client.post("/users/register", json=user).status_code == 201
    token = client.post(
        "/users/login",
        data={"username": user["correo_electronico"], "password": user["password"]},
    ).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_excel_lists_every_sale_of_the_user_only(client, auth_headers):
    _upload(client, auth_headers, _monthly_rows(3))
    _upload(client, _other_user_headers(client), [("Ajeno", 999, "Otra", "2024-01-05")])

    response = client.get("/analytics/export/excel", headers=auth_headers)

    assert response.status_code == 200
    assert 'filename="Reporte_Ventas_test_user.xlsx"' in response.headers["content-disposition"]
    sheet = load_workbook(io.BytesIO(response.content)).active
    rows = list(sheet.iter_rows(values_only=True))
    assert sheet.title == "Historial de Ventas"
    assert rows[0] == ("ID Venta", "Producto", "Monto", "Categoria", "Fecha")
    assert len(rows) == 1 + 6
    assert "Ajeno" not in {row[1] for row in rows}


def test_excel_without_sales_returns_404(client, auth_headers):
    response = client.get("/analytics/export/excel", headers=auth_headers)

    assert response.status_code == 404
    assert response.json()["detail"] == "No hay datos para exportar."


def test_history_pdf_summarizes_user_sales_with_thousands(client, auth_headers):
    _upload(client, auth_headers, _monthly_rows(14))
    _upload(client, auth_headers, [("Caviar", 12345.5, "Gourmet", "2025-02-14")])
    _upload(client, _other_user_headers(client), [("Ajeno", 999, "Otra", "2026-01-05")])

    response = client.get("/analytics/export/pdf", headers=auth_headers)

    _, text = _pdf_text(response)
    assert 'filename="Reporte_Predicta_test_user.pdf"' in response.headers["content-disposition"]
    for section in (
        "Métricas globales",
        "Ventas por categoría",
        "Últimos 12 meses con ventas",
        "Las 20 ventas de mayor monto",
    ):
        assert section in text
    assert "12,345.50" in text
    assert "Febrero 2025" in text
    assert "Ajeno" not in text


def test_history_pdf_size_does_not_grow_with_sales(client, auth_headers):
    rows = [
        (f"Producto {index}", 10 + index, f"Categoria {index % 30}", date(2024, 1 + index % 12, 1 + index % 28))
        for index in range(3000)
    ]
    _upload(client, auth_headers, rows)

    response = client.get("/analytics/export/pdf", headers=auth_headers)

    pages, text = _pdf_text(response)
    assert pages <= 4
    assert "Otras (15 categorías)" in text
    assert len(re.findall(r"Producto \d+ ", text)) == 20


def test_history_pdf_without_sales_returns_404(client, auth_headers):
    response = client.get("/analytics/export/pdf", headers=auth_headers)

    assert response.status_code == 404


@pytest.mark.parametrize(("months", "horizon"), [(24, 12), (12, 6)])
def test_annual_pdf_reports_the_applied_horizon(client, auth_headers, months, horizon):
    _upload(client, auth_headers, _monthly_rows(months, complete=True))

    response = client.get("/analytics/reporte-predictivo-anual-pdf", headers=auth_headers)

    pages, text = _pdf_text(response)
    assert pages == 1
    assert 'filename="Predicta_Reporte_Anual_test_user.pdf"' in response.headers[
        "content-disposition"
    ]
    assert f"Ingreso Acumulado Estimado (Próximos {horizon} meses): $" in text


def test_annual_pdf_warns_when_seasons_are_not_modeled(client, auth_headers):
    _upload(client, auth_headers, _monthly_rows(12, complete=True))

    _, text = _pdf_text(client.get("/analytics/reporte-predictivo-anual-pdf", headers=auth_headers))

    assert "Nota: Con 12 meses completos la proyección es una tendencia" in text


def test_monthly_pdf_for_known_month(client, auth_headers):
    _upload(client, auth_headers, _monthly_rows(14))

    response = client.get("/analytics/reporte-mensual/Mayo", headers=auth_headers)

    pages, text = _pdf_text(response)
    assert pages == 1
    assert 'filename="Predicta_Inferencia_mayo.pdf"' in response.headers["content-disposition"]
    assert "Diagnóstico Gráfico Mensual" in text


def test_monthly_pdf_rejects_unknown_month(client, auth_headers):
    _upload(client, auth_headers, _monthly_rows(3))

    response = client.get("/analytics/reporte-mensual/brumario", headers=auth_headers)

    assert response.status_code == 400
    assert response.json()["detail"] == "El modulo analitico no reconoce el mes 'brumario'."


def test_category_pdf_lists_twelve_projected_months(client, auth_headers):
    _upload(client, auth_headers, _monthly_rows(24, complete=True))

    response = client.get("/analytics/prediccion-categorias/abarrotes", headers=auth_headers)

    _, text = _pdf_text(response)
    assert 'filename="Predicta_abarrotes_Proyeccion.pdf"' in response.headers[
        "content-disposition"
    ]
    assert "TOTAL ESTIMADO (12 MESES)" in text
    for label in ("Enero 2026", "Diciembre 2026"):
        assert label in text


def test_category_pdf_with_short_history_lists_only_the_applied_horizon(client, auth_headers):
    _upload(client, auth_headers, _monthly_rows(8, complete=True))

    _, text = _pdf_text(client.get("/analytics/prediccion-categorias/abarrotes", headers=auth_headers))

    assert "TOTAL ESTIMADO (4 MESES)" in text
    assert "Diciembre 2024" in text
    assert "Enero 2025" not in text


def test_projection_reports_need_six_complete_months(client, auth_headers):
    _upload(client, auth_headers, _monthly_rows(6))

    response = client.get("/analytics/reporte-predictivo-anual-pdf", headers=auth_headers)

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Se necesitan al menos 6 meses completos de ventas para proyectar; hay 5 y faltan 1."
    )


def test_category_pdf_without_sales_in_category_returns_400(client, auth_headers):
    _upload(client, auth_headers, _monthly_rows(3))

    response = client.get("/analytics/prediccion-categorias/ropa", headers=auth_headers)

    assert response.status_code == 400
    assert response.json()["detail"] == "No hay registros historicos para la categoria 'Ropa'."


def test_monthly_labels_use_real_years():
    history = [pd.Timestamp("2024-05-31"), pd.Timestamp("2025-05-31")]

    labels = report_service.comparison_labels(history, pd.Timestamp("2026-05-31"))

    assert labels == ["2024", "2025", "2026 (estimado)"]


def _report_images(content):
    return [image.data for page in PdfReader(io.BytesIO(content)).pages for image in page.images]


def test_concurrent_reports_draw_the_same_charts_as_serial_ones(tmp_path):
    # A file database gives each thread its own connection, as PostgreSQL does in
    # production; the in-memory fixture shares one connection across threads.
    engine = create_engine(
        f"sqlite:///{tmp_path / 'reports.db'}", connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(bind=engine)
    make_session = sessionmaker(bind=engine)
    with make_session() as db:
        user = models.Usuario(
            nombre_usuario="hilos", correo_electronico="hilos@example.com", contrasena_hash="x"
        )
        db.add(user)
        db.flush()
        for producto, monto, categoria, fecha in _monthly_rows(14):
            db.add(
                models.Venta(
                    id_usuario=user.id_usuario,
                    producto=producto,
                    monto=monto,
                    cantidad=1,
                    categoria=categoria,
                    fecha_venta=fecha,
                )
            )
        db.commit()
        user_id = user.id_usuario

    builders = [
        lambda db: report_service.history_pdf(db, user_id, "hilos"),
        lambda db: report_service.annual_forecast_pdf(db, user_id, "hilos"),
        lambda db: report_service.monthly_report_pdf(db, user_id, "mayo"),
        lambda db: report_service.category_forecast_pdf(db, user_id, "abarrotes"),
    ]

    def build(index):
        with make_session() as db:
            return _report_images(builders[index % len(builders)](db).content)

    serial = [build(index) for index in range(len(builders))]
    with ThreadPoolExecutor(max_workers=8) as pool:
        concurrent = list(pool.map(build, range(4 * len(builders))))
    engine.dispose()

    for index, images in enumerate(concurrent):
        assert images == serial[index % len(builders)]
