"""Sales aggregations scoped to one user.

Every function takes the owner's ``user_id`` explicitly and filters by it
before anything else. Totals are computed with ``GROUP BY`` in the database;
only already-aggregated rows reach Python.
"""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Query, Session

from app.ml_models.forecast import daily_predictions
from app.models import models


class InvalidDateRangeError(ValueError):
    """The requested start date is after the end date."""


@dataclass(frozen=True)
class DailySales:
    """Totals of one observed day, shaped like a sale for the forecast module."""

    fecha_venta: date
    monto: Decimal
    cantidad: Decimal


def _user_sales(db: Session, user_id: int, *columns: Any) -> Query:
    """Start a query that can only ever see this user's sales."""
    return db.query(*columns).filter(models.Venta.id_usuario == user_id)


def _apply_date_range(
    query: Query,
    fecha_desde: date | None,
    fecha_hasta: date | None,
) -> Query:
    """Apply inclusive date bounds after the mandatory user filter."""
    if fecha_desde and fecha_hasta and fecha_desde > fecha_hasta:
        raise InvalidDateRangeError("fecha_desde no puede ser posterior a fecha_hasta.")
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
            "categoria": row.categoria,
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
    db: Session, user_id: int, categoria: str | None = None
) -> list[DailySales]:
    """Return amount and units per observed day, oldest first.

    Days without sales are absent, never zero-filled.
    """
    query = _user_sales(
        db,
        user_id,
        models.Venta.fecha_venta,
        func.sum(models.Venta.monto),
        func.sum(func.coalesce(models.Venta.cantidad, 1)),
    )
    if categoria is not None:
        query = query.filter(models.Venta.categoria == categoria)
    rows = query.group_by(models.Venta.fecha_venta).order_by(models.Venta.fecha_venta).all()
    return [
        DailySales(fecha_venta=day, monto=Decimal(amount), cantidad=Decimal(units))
        for day, amount, units in rows
    ]


def sales_page(db: Session, user_id: int, skip: int, limit: int) -> tuple[int, list[models.Venta]]:
    """Return the total count and one page of sales, newest first."""
    base = db.query(models.Venta).filter(models.Venta.id_usuario == user_id)
    total = base.count()
    ventas = base.order_by(models.Venta.fecha_venta.desc()).offset(skip).limit(limit).all()
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


def predict_next_day(db: Session, user_id: int) -> dict[str, Any] | None:
    """Forecast the day after the last sale and store it, or ``None`` without data."""
    daily = daily_sales(db, user_id)
    if len(daily) < 2:
        return None

    next_date, forecasts = daily_predictions(
        [day.fecha_venta for day in daily],
        [float(day.monto) for day in daily],
        [float(day.cantidad) for day in daily],
    )
    amount = forecasts["monto"]
    quantity = forecasts["cantidad"]

    db.add(
        models.Prediccion(
            id_usuario=user_id,
            producto_referencia="GLOBAL",
            cantidad_proyectada=round(quantity.prediction, 2),
            monto_proyectado=round(amount.prediction, 2),
            fecha_proyeccion=next_date,
            precision_estimada=(
                round(amount.metrics["r2"], 2)
                if amount.metrics["r2"] is not None
                else None
            ),
        )
    )
    db.commit()

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
        "mensaje": "Prediccion ajustada: los valores negativos se nivelan a cero.",
    }


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
