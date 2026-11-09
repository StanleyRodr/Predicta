"""Sales aggregations scoped to one user.

Every function takes the owner's ``user_id`` explicitly and filters by it
before anything else. Totals are computed with ``GROUP BY`` in the database;
only already-aggregated rows reach Python.
"""

from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Any, Literal

from sqlalchemy import extract, func
from sqlalchemy.orm import Query, Session

from app.ml_models.forecast import (
    InsufficientHistoryError,
    MonthlyForecast,
    daily_predictions,
    forecast_from_sales,
)
from app.models import models
from app.services.category_service import (
    category_key,
    normalize_category,
    normalize_product,
)

Granularity = Literal["mes", "dia"]


class InvalidDateRangeError(ValueError):
    """The requested start date is after the end date; ``detail`` is safe to show."""

    detail = "fecha_desde no puede ser posterior a fecha_hasta."

    def __init__(self) -> None:
        super().__init__(self.detail)


class ForecastUnavailableError(ValueError):
    """The history cannot support a projection; ``detail`` is safe to show."""

    def __init__(self, detail: str) -> None:
        super().__init__(detail)
        self.detail = detail


@dataclass(frozen=True)
class DailySales:
    """Totals of one observed day, shaped like a sale for the forecast module."""

    fecha_venta: date
    monto: Decimal
    cantidad: Decimal


def _user_sales(db: Session, user_id: int, *columns: Any) -> Query:
    """Start a query that can only ever see this user's sales."""
    return db.query(*columns).filter(models.Venta.id_usuario == user_id)


def _check_date_range(fecha_desde: date | None, fecha_hasta: date | None) -> None:
    if fecha_desde and fecha_hasta and fecha_desde > fecha_hasta:
        raise InvalidDateRangeError


def _apply_date_range(
    query: Query,
    fecha_desde: date | None,
    fecha_hasta: date | None,
) -> Query:
    """Apply inclusive date bounds after the mandatory user filter."""
    _check_date_range(fecha_desde, fecha_hasta)
    if fecha_desde:
        query = query.filter(models.Venta.fecha_venta >= fecha_desde)
    if fecha_hasta:
        query = query.filter(models.Venta.fecha_venta <= fecha_hasta)
    return query


def global_metrics(
    db: Session,
    user_id: int,
    fecha_desde: date | None = None,
    fecha_hasta: date | None = None,
) -> dict[str, float | int]:
    """Return revenue, count, average ticket, and highest sale."""
    row = _apply_date_range(
        _user_sales(
            db,
            user_id,
            func.sum(models.Venta.monto),
            func.count(models.Venta.id_venta),
            func.avg(models.Venta.monto),
            func.max(models.Venta.monto),
        ),
        fecha_desde,
        fecha_hasta,
    ).one()
    total, count, average, highest = row
    return {
        "total_ingresos": float(total or 0),
        "cantidad_operaciones": count,
        "ticket_promedio": round(float(average or 0), 2),
        "venta_mas_alta": float(highest or 0),
    }


def category_breakdown(
    db: Session,
    user_id: int,
    fecha_desde: date | None = None,
    fecha_hasta: date | None = None,
) -> list[dict[str, Any]]:
    """Return revenue and ticket metrics per category, largest revenue first."""
    query = _user_sales(
        db,
        user_id,
        models.Venta.categoria,
        func.sum(models.Venta.monto).label("total_ingresos"),
        func.count(models.Venta.id_venta).label("numero_ventas"),
    )
    rows = (
        _apply_date_range(query, fecha_desde, fecha_hasta)
        .group_by(models.Venta.categoria)
        .all()
    )
    return [
        {
            # Ingestion files uncategorized sales under "General"; older null rows read the same.
            "categoria": row.categoria if row.categoria is not None else normalize_category(None),
            "ingresos_totales": float(row.total_ingresos),
            "cantidad_ventas": row.numero_ventas,
            "ticket_promedio": round(float(row.total_ingresos / row.numero_ventas), 2),
        }
        for row in rows
    ]


def daily_revenue(
    db: Session,
    user_id: int,
    fecha_desde: date | None = None,
    fecha_hasta: date | None = None,
) -> list[dict[str, Any]]:
    """Return revenue and operation count per observed day, oldest first."""
    query = _user_sales(
        db,
        user_id,
        models.Venta.fecha_venta,
        func.sum(models.Venta.monto).label("total_dia"),
        func.count(models.Venta.id_venta).label("num_operaciones"),
    )
    rows = (
        _apply_date_range(query, fecha_desde, fecha_hasta)
        .group_by(models.Venta.fecha_venta)
        .order_by(models.Venta.fecha_venta)
        .all()
    )
    return [
        {
            "fecha": str(row.fecha_venta),
            "ingresos": float(row.total_dia),
            "ventas_realizadas": row.num_operaciones,
        }
        for row in rows
    ]


def daily_sales(
    db: Session,
    user_id: int,
    categorias: Sequence[str] | None = None,
    producto: str | None = None,
) -> list[DailySales]:
    """Return amount and units per observed day, oldest first.

    ``categorias`` holds stored spellings of one category, as ``resolve_category``
    returns them; ``None`` covers every category. ``producto`` is a normalized
    product name within them; ``None`` covers every product. Days without sales
    are absent, never zero-filled.
    """
    query = _user_sales(
        db,
        user_id,
        models.Venta.fecha_venta,
        func.sum(models.Venta.monto),
        func.sum(func.coalesce(models.Venta.cantidad, 1)),
    )
    if categorias is not None:
        query = query.filter(models.Venta.categoria.in_(list(categorias)))
    if producto is not None:
        query = query.filter(models.Venta.producto == producto)
    rows = query.group_by(models.Venta.fecha_venta).order_by(models.Venta.fecha_venta).all()
    return [
        DailySales(fecha_venta=day, monto=Decimal(amount), cantidad=Decimal(units))
        for day, amount, units in rows
    ]


def resolve_category(db: Session, user_id: int, value: str) -> tuple[str, list[str]]:
    """Return a category's display name and every stored spelling of it.

    Matching ignores case, spacing, and accents, also for categories the user
    created, so ``electronica`` finds ``Electrónica``. Rows stored before
    ingestion normalized names (``lacteos``) are found as well.
    """
    wanted = category_key(value)
    stored = [
        name
        for (name,) in _user_sales(db, user_id, models.Venta.categoria).distinct()
        if name is not None and category_key(name) == wanted
    ]
    display = normalize_category(value)
    if stored and display not in stored:
        # Show the user's own spelling, preferring a capitalized one over legacy lowercase.
        display = max(stored, key=lambda name: (name != name.lower(), name))
    return display, stored


def category_products(db: Session, user_id: int, categoria: str) -> tuple[str, list[str]]:
    """Return a category's display name and its products, sorted by name."""
    display, stored = resolve_category(db, user_id, categoria)
    names = (
        _user_sales(db, user_id, models.Venta.producto)
        .filter(models.Venta.categoria.in_(stored))
        .distinct()
        .order_by(models.Venta.producto)
    )
    return display, [name for (name,) in names]


def _point(
    granularidad: Granularity,
    anio: int,
    mes: int,
    dia: int | None,
    categoria: str | None,
    totals: list[Any],
) -> dict[str, Any]:
    periodo = f"{anio:04d}-{mes:02d}" if dia is None else f"{anio:04d}-{mes:02d}-{dia:02d}"
    return {
        "periodo": periodo,
        "anio": anio,
        "mes": mes,
        "dia": dia if granularidad == "dia" else None,
        "categoria": categoria,
        "ingresos": round(float(totals[0]), 2),
        "cantidad": round(float(totals[1]), 2),
        "ventas_realizadas": int(totals[2]),
    }


def sales_series(
    db: Session,
    user_id: int,
    granularidad: Granularity = "mes",
    categoria: str | None = None,
    por_categoria: bool = False,
    fecha_desde: date | None = None,
    fecha_hasta: date | None = None,
) -> tuple[str | None, list[dict[str, Any]]]:
    """Return revenue, units, and sale count per month or day, oldest first.

    Periods without sales are absent, never zero-filled. With ``por_categoria``
    each point also carries its category, and spellings of one category merge.
    Returns the resolved category name, if one was requested, and the points.
    """
    _check_date_range(fecha_desde, fecha_hasta)
    display: str | None = None
    stored: list[str] = []
    if categoria is not None:
        display, stored = resolve_category(db, user_id, categoria)
        if not stored:
            return display, []

    if granularidad == "mes":
        period: list[Any] = [
            extract("year", models.Venta.fecha_venta),
            extract("month", models.Venta.fecha_venta),
        ]
    else:
        period = [models.Venta.fecha_venta]
    groups = period + ([models.Venta.categoria] if por_categoria else [])

    query = _user_sales(
        db,
        user_id,
        *groups,
        func.sum(models.Venta.monto),
        func.sum(func.coalesce(models.Venta.cantidad, 1)),
        func.count(models.Venta.id_venta),
    )
    if stored:
        query = query.filter(models.Venta.categoria.in_(stored))
    rows = _apply_date_range(query, fecha_desde, fecha_hasta).group_by(*groups).all()

    merged: dict[tuple[int, int, int | None, str | None], list[Any]] = defaultdict(
        lambda: [Decimal(0), Decimal(0), 0]
    )
    for row in rows:
        if granularidad == "mes":
            key_period: tuple[int, int, int | None] = (int(row[0]), int(row[1]), None)
        else:
            day = row[0]
            key_period = (day.year, day.month, day.day)
        name = normalize_category(row[len(period)]) if por_categoria else None
        totals = merged[(*key_period, name)]
        for index, value in enumerate(row[len(groups):]):
            totals[index] += Decimal(str(value or 0)) if index < 2 else int(value or 0)

    ordered = sorted(merged.items(), key=lambda item: (item[0][:3], item[0][3] or ""))
    return display, [
        _point(granularidad, anio, mes, dia, name, totals)
        for (anio, mes, dia, name), totals in ordered
    ]


def sales_page(
    db: Session,
    user_id: int,
    skip: int,
    limit: int,
    categoria: str | None = None,
    fecha_desde: date | None = None,
    fecha_hasta: date | None = None,
    producto: str | None = None,
) -> tuple[int, list[models.Venta]]:
    """Return the total count and one page of sales, newest first.

    ``producto`` narrows ``categoria`` to one product; callers require both.
    """
    base = _apply_date_range(
        db.query(models.Venta).filter(models.Venta.id_usuario == user_id),
        fecha_desde,
        fecha_hasta,
    )
    if categoria is not None:
        _, stored = resolve_category(db, user_id, categoria)
        base = base.filter(models.Venta.categoria.in_(stored))
    if producto is not None:
        base = base.filter(models.Venta.producto == normalize_product(producto))
    total = base.count()
    ventas = (
        base.order_by(models.Venta.fecha_venta.desc(), models.Venta.id_venta.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return total, ventas


def sales_for_export(db: Session, user_id: int) -> list[Any]:
    """Return the columns of every sale the Excel export lists."""
    return _user_sales(
        db,
        user_id,
        models.Venta.id_venta,
        models.Venta.producto,
        models.Venta.monto,
        models.Venta.categoria,
        models.Venta.fecha_venta,
    ).all()


def predict_next_day(db: Session, user_id: int) -> dict[str, Any]:
    """Forecast the day after the last sale without storing anything."""
    daily = daily_sales(db, user_id)
    if len(daily) < 2:
        raise ForecastUnavailableError("Se necesitan al menos 2 días con ventas para proyectar.")

    next_date, forecasts = daily_predictions(
        [day.fecha_venta for day in daily],
        [float(day.monto) for day in daily],
        [float(day.cantidad) for day in daily],
    )
    amount = forecasts["monto"]
    quantity = forecasts["cantidad"]
    return {
        "proxima_fecha": str(next_date),
        "monto_predicho": round(amount.prediction, 2),
        "cantidad_predicha": round(quantity.prediction, 2),
        "monto_original_crudo": round(amount.raw_prediction, 2),
        "intervalos_prediccion": {
            "monto": {"inferior": round(amount.lower, 2), "superior": round(amount.upper, 2)},
            "cantidad": {
                "inferior": round(quantity.lower, 2),
                "superior": round(quantity.upper, 2),
            },
        },
        "metricas": {"monto": amount.metrics, "cantidad": quantity.metrics},
        "mensaje": "Predicción ajustada: los valores negativos se nivelan a cero.",
    }


def monthly_projection(
    db: Session, user_id: int, categoria: str | None = None, producto: str | None = None
) -> tuple[str | None, str | None, MonthlyForecast]:
    """Project the user's monthly sales overall, for a category, or for one of its products.

    ``producto`` narrows ``categoria``; callers require both. Returns the
    category's and product's display names (``None`` when not requested) and the
    forecast, without storing. Raises ``ForecastUnavailableError`` when no
    projection is possible.
    """
    display: str | None = None
    stored: list[str] | None = None
    product: str | None = None
    if categoria is not None:
        display, stored = resolve_category(db, user_id, categoria)
        if not stored:
            raise ForecastUnavailableError(f"No hay ventas de la categoría '{display}' para proyectar.")
    if producto is not None:
        product = normalize_product(producto)
    daily = daily_sales(db, user_id, stored, product)
    if not daily:
        if product is not None:
            raise ForecastUnavailableError(
                f"No hay ventas del producto '{product}' en la categoría '{display}' para proyectar."
            )
        raise ForecastUnavailableError("No hay ventas para proyectar.")
    try:
        return display, product, forecast_from_sales(daily)
    except InsufficientHistoryError as exc:
        raise ForecastUnavailableError(exc.detail) from exc


def top_sales(db: Session, user_id: int, limit: int) -> list[Any]:
    """Return the user's highest sales, newest first among equal amounts."""
    return (
        _user_sales(
            db,
            user_id,
            models.Venta.producto,
            models.Venta.categoria,
            models.Venta.fecha_venta,
            models.Venta.monto,
        )
        .order_by(models.Venta.monto.desc(), models.Venta.fecha_venta.desc())
        .limit(limit)
        .all()
    )
