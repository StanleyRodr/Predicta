"""Analytics, prediction, and report endpoints.

Routes only validate input, call a service, and shape the HTTP response.
Aggregations live in ``analytics_service``; Excel and PDF files in
``report_service``.
"""

from collections.abc import Callable
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models import models
from app.services import analytics_service, report_service

router = APIRouter(prefix="/analytics", tags=["Analytics"])

DATE_FROM = Query(None, description="Fecha inicial inclusiva en formato YYYY-MM-DD.")
DATE_TO = Query(None, description="Fecha final inclusiva en formato YYYY-MM-DD.")


def _in_date_range[T](build: Callable[[], T]) -> T:
    """Turn an inverted date range into the public 422 response."""
    try:
        return build()
    except analytics_service.InvalidDateRangeError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


def _download(build: Callable[[], report_service.Report]) -> Response:
    """Wrap a generated report in a downloadable response."""
    try:
        report = build()
    except report_service.ReportError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc
    return Response(
        content=report.content,
        media_type=report.media_type,
        headers={
            "Content-Disposition": f'attachment; filename="{report.filename}"',
            "Access-Control-Expose-Headers": "Content-Disposition",
        },
    )


# =====================================================================
# Statistics
# =====================================================================


@router.get("/stats")
def global_stats(
    fecha_desde: date | None = DATE_FROM,
    fecha_hasta: date | None = DATE_TO,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user),
) -> dict:
    """Return aggregate revenue, count, average ticket, and max sale."""
    metrics = _in_date_range(
        lambda: analytics_service.global_metrics(
            db, current_user.id_usuario, fecha_desde, fecha_hasta
        )
    )
    return {"usuario": current_user.nombre_usuario, "metricas_globales": metrics}


@router.get("/stats/categories")
def category_stats(
    fecha_desde: date | None = DATE_FROM,
    fecha_hasta: date | None = DATE_TO,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user),
) -> dict:
    """Return revenue and ticket metrics grouped by product category."""
    breakdown = _in_date_range(
        lambda: analytics_service.category_breakdown(
            db, current_user.id_usuario, fecha_desde, fecha_hasta
        )
    )
    return {"usuario": current_user.nombre_usuario, "analisis_por_categoria": breakdown}


@router.get("/stats/temporal")
def temporal_stats(
    fecha_desde: date | None = DATE_FROM,
    fecha_hasta: date | None = DATE_TO,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user),
) -> dict:
    """Return daily revenue evolution ordered chronologically."""
    evolucion = _in_date_range(
        lambda: analytics_service.daily_revenue(
            db, current_user.id_usuario, fecha_desde, fecha_hasta
        )
    )
    return {"usuario": current_user.nombre_usuario, "evolucion_diaria": evolucion}


@router.get("/ventas")
def sales_history(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user),
) -> dict:
    """Return a paginated slice of the user's sales, newest first."""
    total, ventas = analytics_service.sales_page(db, current_user.id_usuario, skip, limit)
    return {
        "usuario": current_user.nombre_usuario,
        "total_registros": total,
        "pagina_actual": (skip // limit) + 1,
        "total_paginas": (total + limit - 1) // limit,
        "registros": [
            {
                "id": v.id_venta,
                "producto": v.producto,
                "monto": float(v.monto),
                "categoria": v.categoria,
                "fecha": v.fecha_venta.strftime("%Y-%m-%d %H:%M:%S"),
            }
            for v in ventas
        ],
    }


# =====================================================================
# Predictions
# =====================================================================


@router.get("/predict")
def predict_next_day(
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user),
) -> dict:
    """Forecast the revenue for the day following the last recorded sale."""
    forecast = analytics_service.predict_next_day(db, current_user.id_usuario)
    if forecast is None:
        return {"error": "Se necesitan al menos 2 dias de datos para predecir."}
    return {"usuario": current_user.nombre_usuario, **forecast}


# =====================================================================
# Reports
# =====================================================================


@router.get("/export/excel")
def export_excel(
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user),
) -> Response:
    """Return the user's full sales history as an .xlsx file."""
    return _download(
        lambda: report_service.sales_excel(
            db, current_user.id_usuario, current_user.nombre_usuario
        )
    )


@router.get("/export/pdf")
def export_pdf(
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user),
) -> Response:
    """Return a historical PDF report."""
    return _download(
        lambda: report_service.history_pdf(
            db, current_user.id_usuario, current_user.nombre_usuario
        )
    )


@router.get("/reporte-predictivo-anual-pdf")
def annual_forecast_pdf(
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user),
) -> Response:
    """Return a PDF with the next-12-month forecast combined with history."""
    return _download(
        lambda: report_service.annual_forecast_pdf(
            db, current_user.id_usuario, current_user.nombre_usuario
        )
    )


@router.get("/reporte-mensual/{mes}")
def monthly_report_pdf(
    mes: str,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user),
) -> Response:
    """Return a PDF comparing a future month against the same month in past years."""
    return _download(
        lambda: report_service.monthly_report_pdf(db, current_user.id_usuario, mes)
    )


@router.get("/prediccion-categorias/{categoria}")
def category_forecast_pdf(
    categoria: str,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user),
) -> Response:
    """Return a PDF with the 12-month forecast filtered to a single category."""
    return _download(
        lambda: report_service.category_forecast_pdf(db, current_user.id_usuario, categoria)
    )
