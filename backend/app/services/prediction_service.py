"""Monthly projections as API payloads, and the batches users choose to save.

Reading a projection never writes. Saving recomputes the projection on the
server from the user's own sales, so no client-sent value is ever stored.
Every query is filtered by the owner's ``id_usuario``.
"""

import math
import uuid
from decimal import Decimal
from typing import Any

import pandas as pd
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.ml_models.forecast import MonthlyForecast
from app.models import models
from app.services import analytics_service

GLOBAL_REFERENCE = "GLOBAL"


def _period(moment: pd.Timestamp) -> str:
    return f"{moment.year:04d}-{moment.month:02d}"


def _clean(value: Any) -> Any:
    """JSON has no NaN; an undefined metric is null, never zero."""
    if isinstance(value, float) and math.isnan(value):
        return None
    return value


def forecast_payload(categoria: str | None, forecast: MonthlyForecast) -> dict[str, Any]:
    """Shape a monthly forecast as ``GET /analytics/forecast`` returns it."""
    amount = forecast.objetivos["monto"]
    units = forecast.objetivos["cantidad"]
    partial = forecast.mes_parcial
    return {
        "categoria": categoria,
        "modelo": forecast.modelo,
        "horizonte_aplicado": forecast.horizonte,
        "meses_observados": forecast.meses_observados,
        "advertencia": forecast.advertencia,
        "historial": [
            {"periodo": _period(row.fecha), "monto": round(float(row.monto), 2), "cantidad": round(float(row.cantidad), 2)}
            for row in forecast.historial.itertuples()
        ],
        "mes_parcial": None
        if partial is None
        else {
            "periodo": _period(partial["fecha"]),
            "monto": round(float(partial["monto"]), 2),
            "cantidad": round(float(partial["cantidad"]), 2),
        },
        "proyeccion": [
            {
                "periodo": _period(money.fecha),
                "extrapolacion": money.extrapolacion,
                "monto": {
                    "prediccion": round(money.prediccion, 2),
                    "inferior": round(money.inferior, 2),
                    "superior": round(money.superior, 2),
                },
                "cantidad": {
                    "prediccion": round(unit.prediccion, 2),
                    "inferior": round(unit.inferior, 2),
                    "superior": round(unit.superior, 2),
                },
            }
            for money, unit in zip(amount.puntos, units.puntos, strict=True)
        ],
        "metricas": {
            "monto": {key: _clean(value) for key, value in amount.metricas.items()},
            "cantidad": {key: _clean(value) for key, value in units.metricas.items()},
        },
    }


def _money(value: float) -> Decimal:
    return Decimal(str(round(value, 2)))


def save_projection(db: Session, user_id: int, categoria: str | None) -> dict[str, Any]:
    """Recompute the monthly projection and store one row per projected month."""
    display, forecast = analytics_service.monthly_projection(db, user_id, categoria)
    amount = forecast.objetivos["monto"]
    units = forecast.objetivos["cantidad"]
    batch = uuid.uuid4().hex
    rows = [
        models.Prediccion(
            id_usuario=user_id,
            lote=batch,
            tipo="mensual",
            categoria=display,
            producto_referencia=display or GLOBAL_REFERENCE,
            fecha_proyeccion=money.fecha.date(),
            monto_proyectado=_money(money.prediccion),
            monto_inferior=_money(money.inferior),
            monto_superior=_money(money.superior),
            cantidad_proyectada=_money(unit.prediccion),
            cantidad_inferior=_money(unit.inferior),
            cantidad_superior=_money(unit.superior),
            modelo=forecast.modelo,
            horizonte=forecast.horizonte,
            extrapolacion=money.extrapolacion,
            r2_validacion=_clean(amount.metricas["r2"]),
            wape_validacion=_clean(amount.metricas["wape"]),
        )
        for money, unit in zip(amount.puntos, units.puntos, strict=True)
    ]
    db.add_all(rows)
    db.commit()
    return _batch(rows)


def _decimal(value: Decimal | None) -> float | None:
    return None if value is None else float(value)


def _batch(rows: list[models.Prediccion]) -> dict[str, Any]:
    first = rows[0]
    return {
        "lote": first.lote,
        "tipo": first.tipo,
        "categoria": first.categoria,
        "modelo": first.modelo,
        "horizonte": first.horizonte,
        "r2_validacion": first.r2_validacion,
        "wape_validacion": first.wape_validacion,
        "fecha_creacion": first.fecha_creacion,
        "puntos": [
            {
                "fecha_proyeccion": row.fecha_proyeccion,
                "extrapolacion": row.extrapolacion,
                "monto_proyectado": _decimal(row.monto_proyectado),
                "monto_inferior": _decimal(row.monto_inferior),
                "monto_superior": _decimal(row.monto_superior),
                "cantidad_proyectada": _decimal(row.cantidad_proyectada),
                "cantidad_inferior": _decimal(row.cantidad_inferior),
                "cantidad_superior": _decimal(row.cantidad_superior),
            }
            for row in sorted(rows, key=lambda row: row.fecha_proyeccion)
        ],
    }


def list_batches(db: Session, user_id: int, skip: int, limit: int) -> tuple[int, list[dict[str, Any]]]:
    """Return how many batches the user saved and one page of them, newest first."""
    owned = db.query(models.Prediccion).filter(models.Prediccion.id_usuario == user_id)
    total = owned.with_entities(func.count(func.distinct(models.Prediccion.lote))).scalar() or 0
    newest = func.max(models.Prediccion.fecha_creacion)
    page = [
        lote
        for (lote,) in owned.with_entities(models.Prediccion.lote)
        .group_by(models.Prediccion.lote)
        .order_by(newest.desc(), func.max(models.Prediccion.id_prediccion).desc())
        .offset(skip)
        .limit(limit)
    ]
    if not page:
        return total, []
    grouped: dict[str, list[models.Prediccion]] = {lote: [] for lote in page}
    for row in owned.filter(models.Prediccion.lote.in_(page)):
        grouped[row.lote].append(row)
    return total, [_batch(grouped[lote]) for lote in page]
