"""Analytics, prediction, and report endpoints.

Routes only validate input, call a service, and shape the HTTP response.
Aggregations live in ``analytics_service``; Excel and PDF files in
``report_service``; saved forecasts in ``prediction_service``. No GET writes.
"""

import re
import unicodedata
from collections.abc import Callable
from datetime import date
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Request
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.rate_limit import COMPUTE_LIMIT, limiter
from app.models import models
from app.schemas import schemas
from app.services import analytics_service, prediction_service, report_service

router = APIRouter(prefix="/analytics", tags=["Analytics"])

DATE_FROM = Query(None, description="Fecha inicial inclusiva en formato YYYY-MM-DD.")
DATE_TO = Query(None, description="Fecha final inclusiva en formato YYYY-MM-DD.")
CATEGORY = Query(
    None,
    max_length=schemas.MAX_CATEGORY_LENGTH,
    pattern=schemas.NO_CONTROL_CHARACTERS,
    description="Categoría; no distingue mayúsculas, espacios ni tildes.",
)
PRODUCT = Query(
    None,
    max_length=schemas.MAX_PRODUCT_LENGTH,
    pattern=schemas.NO_CONTROL_CHARACTERS,
    description="Producto de la categoría; requiere categoria. No distingue mayúsculas ni espacios.",
)


def _require_category(categoria: str | None, producto: str | None) -> None:
    """A product is always chosen within its category."""
    if producto is not None and categoria is None:
        raise HTTPException(status_code=422, detail=schemas.PRODUCT_NEEDS_CATEGORY)


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


def content_disposition(filename: str) -> str:
    """Attachment header that survives non-ASCII names (RFC 6266 / RFC 5987).

    ``filename`` is an ASCII fallback without accents or unsafe characters;
    ``filename*`` carries the exact UTF-8 name for browsers that support it.
    """
    ascii_name = unicodedata.normalize("NFKD", filename).encode("ascii", "ignore").decode("ascii")
    ascii_name = re.sub(r"[^A-Za-z0-9._-]", "_", ascii_name) or "reporte"
    return f"attachment; filename=\"{ascii_name}\"; filename*=UTF-8''{quote(filename, safe='')}"


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
            "Content-Disposition": content_disposition(report.filename),
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
    """Return aggregate revenue, count, average ticket, max sale, and monthly growth."""
    metrics = _in_date_range(
        lambda: analytics_service.global_metrics(
            db, current_user.id_usuario, fecha_desde, fecha_hasta
        )
    )
    growth = analytics_service.monthly_growth(db, current_user.id_usuario, fecha_desde, fecha_hasta)
    return {
        "usuario": current_user.nombre_usuario,
        "metricas_globales": metrics,
        "crecimiento_mensual": growth,
    }


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


@router.get("/productos", response_model=schemas.ProductListResponse)
def category_products(
    categoria: str = Query(
        ...,
        max_length=schemas.MAX_CATEGORY_LENGTH,
        pattern=schemas.NO_CONTROL_CHARACTERS,
        description="Categoría; no distingue mayúsculas, espacios ni tildes.",
    ),
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user),
) -> dict:
    """Return the products the user sold within one category, sorted by name."""
    display, products = analytics_service.category_products(db, current_user.id_usuario, categoria)
    return {"usuario": current_user.nombre_usuario, "categoria": display, "productos": products}


@router.get("/ventas", response_model=schemas.SalesPageResponse)
def sales_history(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=200),
    categoria: str | None = CATEGORY,
    producto: str | None = PRODUCT,
    fecha_desde: date | None = DATE_FROM,
    fecha_hasta: date | None = DATE_TO,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user),
) -> dict:
    """Return a paginated slice of the user's sales, newest first."""
    _require_category(categoria, producto)
    total, ventas = _in_date_range(
        lambda: analytics_service.sales_page(
            db, current_user.id_usuario, skip, limit, categoria, fecha_desde, fecha_hasta, producto
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
@limiter.limit(COMPUTE_LIMIT)
def predict_next_day(
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user),
) -> dict:
    """Forecast the day after the last recorded sale; nothing is stored."""
    forecast = _forecast(lambda: analytics_service.predict_next_day(db, current_user.id_usuario))
    return {"usuario": current_user.nombre_usuario, **forecast}


@router.get("/forecast", response_model=schemas.MonthlyForecastResponse)
@limiter.limit(COMPUTE_LIMIT)
def monthly_forecast(
    request: Request,
    categoria: str | None = CATEGORY,
    producto: str | None = PRODUCT,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user),
) -> dict:
    """Return history, monthly projection, intervals, and validation metrics; nothing is stored."""
    _require_category(categoria, producto)
    category, product, forecast = _forecast(
        lambda: analytics_service.monthly_projection(
            db, current_user.id_usuario, categoria, producto
        )
    )
    payload = prediction_service.forecast_payload(category, product, forecast)
    return {"usuario": current_user.nombre_usuario, **payload}


@router.post("/predicciones", response_model=schemas.SavedBatch, status_code=201)
@limiter.limit(COMPUTE_LIMIT)
def save_prediction(
    request: Request,
    payload: schemas.SavePredictionRequest,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user),
) -> dict:
    """Recompute the monthly projection on the server and save every month as one batch."""
    return _forecast(
        lambda: prediction_service.save_projection(
            db, current_user.id_usuario, payload.categoria, payload.producto
        )
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
@limiter.limit(COMPUTE_LIMIT)
def export_excel(
    request: Request,
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
@limiter.limit(COMPUTE_LIMIT)
def export_pdf(
    request: Request,
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
@limiter.limit(COMPUTE_LIMIT)
def annual_forecast_pdf(
    request: Request,
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
@limiter.limit(COMPUTE_LIMIT)
def monthly_report_pdf(
    request: Request,
    mes: str = Path(..., max_length=20, pattern=schemas.NO_CONTROL_CHARACTERS),
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user),
) -> Response:
    """Return a PDF comparing a future month against the same month in past years."""
    return _download(
        lambda: report_service.monthly_report_pdf(db, current_user.id_usuario, mes)
    )


@router.get("/prediccion-categorias/{categoria}")
@limiter.limit(COMPUTE_LIMIT)
def category_forecast_pdf(
    request: Request,
    categoria: str = Path(
        ..., max_length=schemas.MAX_CATEGORY_LENGTH, pattern=schemas.NO_CONTROL_CHARACTERS
    ),
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user),
) -> Response:
    """Return a PDF with the 12-month forecast filtered to a single category."""
    return _download(
        lambda: report_service.category_forecast_pdf(db, current_user.id_usuario, categoria)
    )
