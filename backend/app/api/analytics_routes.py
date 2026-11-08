"""Analytics, prediction, and report endpoints.

Routes only validate input, call a service, and shape the HTTP response.
Aggregations live in ``analytics_service``; Excel and PDF files in
``report_service``; saved forecasts in ``prediction_service``. No GET writes.
"""

from collections.abc import Callable
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models import models
from app.schemas import schemas
from app.services import analytics_service, prediction_service, report_service

router = APIRouter(prefix="/analytics", tags=["Analytics"])

DATE_FROM = Query(None, description="Fecha inicial inclusiva en formato YYYY-MM-DD.")
DATE_TO = Query(None, description="Fecha final inclusiva en formato YYYY-MM-DD.")
CATEGORY = Query(
    None, description="Categoría; no distingue mayúsculas, espacios ni tildes."
)


def _in_date_range[T](build: Callable[[], T]) -> T:
    """Turn an inverted date range into the public 422 response."""
    try:
        return build()
    except analytics_service.InvalidDateRangeError as exc:
        raise HTTPException(status_code=422, detail=exc.detail) from exc


def _forecast[T](build: Callable[[], T]) -> T:
    """Turn a history that cannot be projected into the public 422 response."""
    try:
        return build()
    except analytics_service.ForecastUnavailableError as exc:
        raise HTTPException(status_code=422, detail=exc.detail) from exc


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


@router.get("/stats", response_model=schemas.GlobalStatsResponse)
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


@router.get("/stats/categories", response_model=schemas.CategoryStatsResponse)
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


@router.get("/stats/temporal", response_model=schemas.TemporalStatsResponse)
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


@router.get("/stats/series", response_model=schemas.SeriesResponse)
def sales_series(
    granularidad: analytics_service.Granularity = Query(
        "mes", description="mes agrupa por año y mes; dia, por fecha."
    ),
    categoria: str | None = CATEGORY,
    por_categoria: bool = Query(
        False, description="Separa cada periodo por categoría para compararlas."
    ),
    fecha_desde: date | None = DATE_FROM,
    fecha_hasta: date | None = DATE_TO,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user),
) -> dict:
    """Return sales totals per month or per day, overall or by category."""
    resolved, points = _in_date_range(
        lambda: analytics_service.sales_series(
            db,
            current_user.id_usuario,
            granularidad,
            categoria,
            por_categoria,
            fecha_desde,
            fecha_hasta,
        )
    )
    return {
        "usuario": current_user.nombre_usuario,
        "granularidad": granularidad,
        "categoria": resolved,
        "por_categoria": por_categoria,
        "puntos": points,
    }


@router.get("/ventas", response_model=schemas.SalesPageResponse)
def sales_history(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=200),
    categoria: str | None = CATEGORY,
    fecha_desde: date | None = DATE_FROM,
    fecha_hasta: date | None = DATE_TO,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user),
) -> dict:
    """Return a paginated slice of the user's sales, newest first."""
    total, ventas = _in_date_range(
        lambda: analytics_service.sales_page(
            db, current_user.id_usuario, skip, limit, categoria, fecha_desde, fecha_hasta
        )
    )
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


@router.get("/predict", response_model=schemas.DailyForecastResponse)
def predict_next_day(
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user),
) -> dict:
    """Forecast the day after the last recorded sale; nothing is stored."""
    forecast = _forecast(lambda: analytics_service.predict_next_day(db, current_user.id_usuario))
    return {"usuario": current_user.nombre_usuario, **forecast}


@router.get("/forecast", response_model=schemas.MonthlyForecastResponse)
def monthly_forecast(
    categoria: str | None = CATEGORY,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user),
) -> dict:
    """Return history, monthly projection, intervals, and validation metrics; nothing is stored."""
    resolved, forecast = _forecast(
        lambda: analytics_service.monthly_projection(db, current_user.id_usuario, categoria)
    )
    return {"usuario": current_user.nombre_usuario, **prediction_service.forecast_payload(resolved, forecast)}


@router.post("/predicciones", response_model=schemas.SavedBatch, status_code=201)
def save_prediction(
    payload: schemas.SavePredictionRequest,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user),
) -> dict:
    """Recompute the monthly projection on the server and save every month as one batch."""
    return _forecast(
        lambda: prediction_service.save_projection(db, current_user.id_usuario, payload.categoria)
    )


@router.get("/predicciones", response_model=schemas.SavedBatchPage)
def saved_predictions(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user),
) -> dict:
    """Return the user's saved projections, newest batch first."""
    total, batches = prediction_service.list_batches(db, current_user.id_usuario, skip, limit)
    return {
        "usuario": current_user.nombre_usuario,
        "total_lotes": total,
        "pagina_actual": (skip // limit) + 1,
        "total_paginas": (total + limit - 1) // limit,
        "lotes": batches,
    }


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
