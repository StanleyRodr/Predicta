"""Analytics, prediction, and report endpoints.

Routes are organized in three groups:
- Statistics (global, by category, temporal)
- Predictions (linear regression with monthly seasonality)
- Reports (Excel and PDF exports)
"""

import io
import os
import tempfile
from datetime import timedelta

import matplotlib
import numpy as np
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response, StreamingResponse
from fpdf import FPDF
from matplotlib import pyplot as plt
from matplotlib import dates as mdates
from sklearn.linear_model import LinearRegression
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models import models

# Backend 'Agg' must be set before pyplot is imported to avoid the
# library trying to open a display when running headless.
matplotlib.use("Agg")

router = APIRouter(prefix="/analytics", tags=["Analytics"])

# =====================================================================
# Statistics
# =====================================================================


@router.get("/stats")
def global_stats(
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user),
) -> dict:
    """Return aggregate revenue, count, average ticket, and max sale."""
    base = db.query(models.Venta).filter(
        models.Venta.id_usuario == current_user.id_usuario
    )
    total_ingresos = base.with_entities(func.sum(models.Venta.monto)).scalar() or 0
    total_ventas = base.count()
    promedio_venta = base.with_entities(func.avg(models.Venta.monto)).scalar() or 0
    venta_maxima = base.with_entities(func.max(models.Venta.monto)).scalar() or 0

    return {
        "usuario": current_user.nombre_usuario,
        "metricas_globales": {
            "total_ingresos": float(total_ingresos),
            "cantidad_operaciones": total_ventas,
            "ticket_promedio": round(float(promedio_venta), 2),
            "venta_mas_alta": float(venta_maxima),
        },
    }


@router.get("/stats/categories")
def category_stats(
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user),
) -> dict:
    """Return revenue and ticket metrics grouped by product category."""
    rows = (
        db.query(
            models.Venta.categoria,
            func.sum(models.Venta.monto).label("total_ingresos"),
            func.count(models.Venta.id_venta).label("numero_ventas"),
        )
        .filter(models.Venta.id_usuario == current_user.id_usuario)
        .group_by(models.Venta.categoria)
        .all()
    )

    breakdown = [
        {
            "categoria": r.categoria,
            "ingresos_totales": float(r.total_ingresos),
            "cantidad_ventas": r.numero_ventas,
            "ticket_promedio": round(float(r.total_ingresos / r.numero_ventas), 2),
        }
        for r in rows
    ]
    return {"usuario": current_user.nombre_usuario, "analisis_por_categoria": breakdown}


@router.get("/stats/temporal")
def temporal_stats(
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user),
) -> dict:
    """Return daily revenue evolution ordered chronologically."""
    rows = (
        db.query(
            func.date(models.Venta.fecha_venta).label("fecha"),
            func.sum(models.Venta.monto).label("total_dia"),
            func.count(models.Venta.id_venta).label("num_operaciones"),
        )
        .filter(models.Venta.id_usuario == current_user.id_usuario)
        .group_by(func.date(models.Venta.fecha_venta))
        .order_by(func.date(models.Venta.fecha_venta))
        .all()
    )

    evolucion = [
        {
            "fecha": str(r.fecha),
            "ingresos": float(r.total_dia),
            "ventas_realizadas": r.num_operaciones,
        }
        for r in rows
    ]
    return {"usuario": current_user.nombre_usuario, "evolucion_diaria": evolucion}


@router.get("/ventas")
def sales_history(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user),
) -> dict:
    """Return a paginated slice of the user's sales, newest first."""
    base = db.query(models.Venta).filter(
        models.Venta.id_usuario == current_user.id_usuario
    )
    total = base.count()
    ventas = (
        base.order_by(models.Venta.fecha_venta.desc())
        .offset(skip)
        .limit(limit)
        .all()
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
# Prediction helpers
# =====================================================================

# Business months are mapped to fixed Spanish names used by the
# monthly report endpoint.
MONTH_NAMES = [
    "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre",
]

# Aliases accepted by the monthly report endpoint (URL-friendly).
MONTH_ALIASES: dict[str, int] = {name.lower(): idx + 1 for idx, name in enumerate(MONTH_NAMES)}

# Canonical category names accepted by the category report endpoint.
CATEGORY_ALIASES: dict[str, str] = {
    "abarrotes": "Abarrotes",
    "limpieza": "Limpieza",
    "lacteos": "Lácteos",
    "lácteos": "Lácteos",
    "bebidas": "Bebidas",
    "cuidado-personal": "Cuidado Personal",
    "cuidado personal": "Cuidado Personal",
}


def _build_seasonal_features(months_index: np.ndarray, calendar_months: pd.Series) -> pd.DataFrame:
    """Construct the design matrix: trend + 12 monthly dummy variables."""
    features = pd.DataFrame({"mes_indice": months_index})
    for m in range(1, 13):
        features[f"mes_{m}"] = (calendar_months == m).astype(int)
    return features


def _monthly_aggregates(ventas: list[models.Venta]) -> pd.DataFrame:
    """Resample raw sales into a monthly sum-indexed dataframe."""
    df = pd.DataFrame(
        [{"fecha": v.fecha_venta, "monto": float(v.monto)} for v in ventas]
    )
    df["fecha"] = pd.to_datetime(df["fecha"])
    return df.set_index("fecha").resample("ME")["monto"].sum().reset_index()


# =====================================================================
# Predictions
# =====================================================================


@router.get("/predict")
def predict_next_day(
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user),
) -> dict:
    """Forecast the revenue for the day following the last recorded sale."""
    rows = (
        db.query(
            func.date(models.Venta.fecha_venta).label("fecha"),
            func.sum(models.Venta.monto).label("total_dia"),
        )
        .filter(models.Venta.id_usuario == current_user.id_usuario)
        .group_by(func.date(models.Venta.fecha_venta))
        .order_by(func.date(models.Venta.fecha_venta))
        .all()
    )

    if len(rows) < 2:
        return {"error": "Se necesitan al menos 2 dias de datos para predecir."}

    # (fecha - primera_fecha).days keeps the regression input small
    # and stable compared to using toordinal() (which is ~738000 for
    # recent dates and degrades float precision).
    first_date = rows[0].fecha
    X = np.array([[(r.fecha - first_date).days] for r in rows])
    y = np.array([float(r.total_dia) for r in rows])

    model = LinearRegression().fit(X, y)

    last_date = rows[-1].fecha
    next_date = last_date + timedelta(days=1)
    predicted = float(model.predict([[(next_date - first_date).days]])[0])
    monto_final = max(0.0, predicted)

    return {
        "usuario": current_user.nombre_usuario,
        "proxima_fecha": str(next_date),
        "monto_predicho": round(monto_final, 2),
        "monto_original_crudo": round(predicted, 2),
        "mensaje": "Prediccion ajustada: los valores negativos se nivelan a cero.",
    }


# =====================================================================
# PDF report helpers
# =====================================================================


class _PDFReport(FPDF):
    """FPDF subclass with Predicta branding (header + footer)."""

    def header(self) -> None:
        self.set_font("Arial", "B", 15)
        self.cell(0, 10, "Predicta - Reporte", 0, 1, "C")
        self.set_draw_color(0, 80, 180)
        self.line(10, 22, 200, 22)
        self.ln(10)

    def footer(self) -> None:
        self.set_y(-15)
        self.set_font("Arial", "I", 8)
        self.cell(0, 10, f"Pagina {self.page_no()}", 0, 0, "C")


def _new_fig(*, figsize: tuple[float, float] = (8, 4)) -> tuple[object, object]:
    """Return a fresh matplotlib figure/axes pair."""
    return plt.subplots(figsize=figsize)


def _save_fig_to_temp(fig: object, *, dpi: int = 150) -> str:
    """Persist a matplotlib figure to a temporary PNG and return its path."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
        fig.savefig(tmp.name, format="png", dpi=dpi, bbox_inches="tight")
        path = tmp.name
    plt.close(fig)
    return path


def _build_pdf_response(
    pdf: FPDF, *, filename: str, media_type: str = "application/pdf"
) -> Response:
    """Wrap an FPDF document in a downloadable HTTP response."""
    return Response(
        content=bytes(pdf.output()),
        media_type=media_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Access-Control-Expose-Headers": "Content-Disposition",
        },
    )


# =====================================================================
# Excel & basic PDF reports
# =====================================================================


@router.get("/export/excel")
def export_excel(
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user),
) -> StreamingResponse:
    """Return the user's full sales history as an .xlsx file."""
    ventas = (
        db.query(models.Venta)
        .filter(models.Venta.id_usuario == current_user.id_usuario)
        .all()
    )
    if not ventas:
        raise HTTPException(status_code=404, detail="No hay datos para exportar.")

    df = pd.DataFrame(
        {
            "ID Venta": v.id_venta,
            "Producto": v.producto,
            "Monto": float(v.monto),
            "Categoria": v.categoria,
            "Fecha": v.fecha_venta.strftime("%Y-%m-%d %H:%M:%S"),
        }
        for v in ventas
    )

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Historial de Ventas")
    output.seek(0)

    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f'attachment; filename="Reporte_Ventas_{current_user.nombre_usuario}.xlsx"',
            "Access-Control-Expose-Headers": "Content-Disposition",
        },
    )


@router.get("/export/pdf")
def export_pdf(
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user),
) -> Response:
    """Return a historical PDF report with a daily-sales line chart."""
    ventas = (
        db.query(models.Venta)
        .filter(models.Venta.id_usuario == current_user.id_usuario)
        .all()
    )
    if not ventas:
        raise HTTPException(status_code=404, detail="No hay datos para generar el reporte.")

    daily = (
        db.query(
            func.date(models.Venta.fecha_venta).label("fecha"),
            func.sum(models.Venta.monto).label("total"),
        )
        .filter(models.Venta.id_usuario == current_user.id_usuario)
        .group_by(func.date(models.Venta.fecha_venta))
        .order_by(func.date(models.Venta.fecha_venta))
        .all()
    )

    fig, ax = _new_fig()
    ax.plot(
        [str(d.fecha) for d in daily],
        [float(d.total) for d in daily],
        marker="o",
        linestyle="-",
        color="#0050b3",
        linewidth=2,
    )
    ax.set_title("Evolucion de Ventas Diarias", fontsize=12)
    ax.set_ylabel("Monto de Ventas ($)")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    chart_path = _save_fig_to_temp(fig)

    pdf = _PDFReport()
    pdf.add_page()
    pdf.image(chart_path, x=15, y=30, w=180)
    pdf.ln(100)
    os.remove(chart_path)

    col_widths = [15, 65, 25, 40, 45]
    headers = ["ID", "Producto", "Monto", "Categoria", "Fecha"]
    pdf.set_fill_color(230, 230, 230)
    pdf.set_font("Arial", "B", 10)
    for i, header in enumerate(headers):
        pdf.cell(col_widths[i], 10, header, 1, 0, "C", 1)
    pdf.ln()
    pdf.set_font("Arial", size=10)
    for v in ventas:
        pdf.cell(col_widths[0], 10, str(v.id_venta), 1, 0, "C")
        pdf.cell(col_widths[1], 10, v.producto[:28], 1)
        pdf.cell(col_widths[2], 10, f"${v.monto:.2f}", 1, 0, "R")
        pdf.cell(col_widths[3], 10, str(v.categoria), 1)
        pdf.cell(col_widths[4], 10, v.fecha_venta.strftime("%Y-%m-%d %H:%M"), 1)
        pdf.ln()

    return _build_pdf_response(
        pdf, filename=f"Reporte_Predicta_{current_user.nombre_usuario}.pdf"
    )


# =====================================================================
# Annual forecast report
# =====================================================================


@router.get("/reporte-predictivo-anual-pdf")
def annual_forecast_pdf(
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user),
) -> Response:
    """Return a PDF with the next-12-month forecast combined with history."""
    ventas = (
        db.query(models.Venta)
        .filter(models.Venta.id_usuario == current_user.id_usuario)
        .all()
    )
    if not ventas:
        raise HTTPException(status_code=400, detail="No hay datos historicos para procesar.")

    monthly = _monthly_aggregates(ventas)
    if len(monthly) < 2:
        raise HTTPException(
            status_code=400, detail="Muestreo insuficiente para analisis lineal."
        )

    X_train = _build_seasonal_features(
        np.arange(len(monthly)), monthly["fecha"].dt.month
    )
    y_train = monthly["monto"]
    model = LinearRegression().fit(X_train, y_train)

    last_date = monthly["fecha"].max()
    last_amount = float(monthly.iloc[-1]["monto"])
    future_dates = [last_date + pd.DateOffset(months=i) for i in range(1, 13)]
    X_future = _build_seasonal_features(
        np.arange(len(monthly), len(monthly) + 12),
        pd.Series([d.month for d in future_dates]),
    )
    predictions = np.clip(model.predict(X_future), 0.0, None)

    # Anchor the projection to the last real point so the line is continuous.
    chart_dates = [last_date] + future_dates
    chart_values = [last_amount] + list(predictions)

    fig, ax = _new_fig(figsize=(12, 6))
    ax.plot(
        monthly["fecha"], monthly["monto"],
        marker="o", linestyle="-", color="#004aad", linewidth=2,
        label="Historial Operativo (Datos Reales)",
    )
    ax.plot(
        chart_dates, chart_values,
        marker="X", linestyle="--", color="#ff7f0e", linewidth=2,
        label="Proyeccion Estimada (Proximos 12 meses)",
    )
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=6))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    ax.set_title(
        "Predicta - Historial y Proyeccion de la Demanda Global",
        fontsize=14, fontweight="bold", pad=15,
    )
    ax.set_xlabel("Linea de Tiempo Operativa")
    ax.set_ylabel("Ingresos ($)")
    ax.grid(True, linestyle="--", alpha=0.5)
    plt.xticks(rotation=45)
    ax.legend(loc="upper left", fontsize=10)
    plt.tight_layout()
    chart_path = _save_fig_to_temp(fig)

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, txt="Predicta - Planificacion y Proyeccion de la Demanda", ln=True, align="C")
    pdf.set_draw_color(0, 80, 180)
    pdf.line(10, 20, 200, 20)
    pdf.ln(10)
    pdf.set_font("Arial", size=12)
    pdf.cell(
        0, 10,
        txt=f"Ingreso Acumulado Estimado (Proximos 12 meses): ${sum(predictions):,.2f}",
        ln=True,
    )
    pdf.ln(5)
    pdf.image(chart_path, x=10, y=45, w=190)
    os.remove(chart_path)

    return _build_pdf_response(
        pdf, filename=f"Predicta_Reporte_Anual_{current_user.nombre_usuario}.pdf"
    )


# =====================================================================
# Monthly report (by name)
# =====================================================================


@router.get("/reporte-mensual/{mes}")
def monthly_report_pdf(
    mes: str,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user),
) -> Response:
    """Return a PDF with bar comparison of a future month against history."""
    month_key = mes.lower().strip()
    if month_key not in MONTH_ALIASES:
        raise HTTPException(
            status_code=400,
            detail=f"El modulo analitico no reconoce el mes '{mes}'.",
        )
    target_month = MONTH_ALIASES[month_key]

    ventas = (
        db.query(models.Venta)
        .filter(models.Venta.id_usuario == current_user.id_usuario)
        .all()
    )
    if not ventas:
        raise HTTPException(status_code=400, detail="Ecosistema sin registros para entrenamiento.")

    monthly = _monthly_aggregates(ventas)
    if len(monthly) < 2:
        raise HTTPException(status_code=400, detail="Varianza insuficiente para ejecutar regresion.")

    X_train = _build_seasonal_features(
        np.arange(len(monthly)), monthly["fecha"].dt.month
    )
    model = LinearRegression().fit(X_train, monthly["monto"])

    last_date = monthly["fecha"].max()
    projection_date = None
    for i in range(1, 13):
        candidate = last_date + pd.DateOffset(months=i)
        if candidate.month == target_month:
            projection_date = candidate
            steps = i
            break
    if projection_date is None:
        raise HTTPException(
            status_code=400,
            detail="El mes solicitado cae fuera del rango de prevision de 12 meses.",
        )

    X_pred = _build_seasonal_features(
        np.array([len(monthly) + steps - 1]),
        pd.Series([target_month]),
    )
    monto_predicho = max(0.0, float(model.predict(X_pred)[0]))

    historical = monthly[monthly["fecha"].dt.month == target_month]
    labels = [f"Año {i + 1} Real" for i in range(len(historical))]
    values = list(historical["monto"])
    labels.append(f"{projection_date.strftime('%Y-%m')} Est.")
    values.append(monto_predicho)

    fig, ax = _new_fig(figsize=(8, 4.5))
    colors = ["#0050b3"] * (len(values) - 1) + ["#e65100"]
    bars = ax.bar(labels, values, color=colors, edgecolor="black", width=0.6)
    ax.set_title(
        f"Análisis Comparativo Interanual: Periodo {mes.upper()}",
        fontsize=12, fontweight="bold",
    )
    ax.set_ylabel("Volumen de Ingresos ($)")
    ax.grid(True, axis="y", linestyle="--", alpha=0.5)
    for bar in bars:
        ax.annotate(
            f"${bar.get_height():,.2f}",
            xy=(bar.get_x() + bar.get_width() / 2, bar.get_height()),
            xytext=(0, 3), textcoords="offset points",
            ha="center", va="bottom", fontsize=9,
        )
    plt.tight_layout()
    chart_path = _save_fig_to_temp(fig)

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 15)
    pdf.cell(0, 10, txt="Predicta - Diagnostico Grafico Mensual", ln=True, align="C")
    pdf.set_draw_color(0, 80, 180)
    pdf.line(10, 20, 200, 20)
    pdf.ln(15)
    pdf.image(chart_path, x=15, y=35, w=180)
    os.remove(chart_path)

    return _build_pdf_response(pdf, filename=f"Predicta_Inferencia_{month_key}.pdf")


# =====================================================================
# Category forecast report
# =====================================================================


@router.get("/prediccion-categorias/{categoria}")
def category_forecast_pdf(
    categoria: str,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user),
) -> Response:
    """Return a PDF with the 12-month forecast filtered to a single category."""
    cat_key = categoria.lower().strip()
    if cat_key not in CATEGORY_ALIASES:
        raise HTTPException(
            status_code=404,
            detail=f"La categoria '{categoria}' no existe en el catalogo operativo.",
        )
    canonical = CATEGORY_ALIASES[cat_key]

    ventas = (
        db.query(models.Venta)
        .filter(
            models.Venta.id_usuario == current_user.id_usuario,
            models.Venta.categoria == canonical,
        )
        .all()
    )
    if not ventas:
        raise HTTPException(
            status_code=400,
            detail=f"No hay registros historicos para la categoria '{canonical}'.",
        )

    monthly = _monthly_aggregates(ventas)
    if len(monthly) < 2:
        raise HTTPException(
            status_code=400,
            detail="Historial insuficiente para proyeccion lineal en esta categoria.",
        )

    X_train = _build_seasonal_features(
        np.arange(len(monthly)), monthly["fecha"].dt.month
    )
    model = LinearRegression().fit(X_train, monthly["monto"])

    last_date = monthly["fecha"].max()
    last_amount = float(monthly.iloc[-1]["monto"])
    future_dates = [last_date + pd.DateOffset(months=i) for i in range(1, 13)]
    future_labels = [f"{MONTH_NAMES[d.month - 1]} {d.year}" for d in future_dates]
    X_future = _build_seasonal_features(
        np.arange(len(monthly), len(monthly) + 12),
        pd.Series([d.month for d in future_dates]),
    )
    predictions = np.clip(model.predict(X_future), 0.0, None)

    chart_dates = [last_date] + future_dates
    chart_values = [last_amount] + list(predictions)

    fig, ax = _new_fig(figsize=(10, 5.5))
    ax.plot(
        monthly["fecha"], monthly["monto"],
        marker="o", linestyle="-", color="#2c7a2c", linewidth=2,
        label=f"Historial: {canonical}",
    )
    ax.plot(
        chart_dates, chart_values,
        marker="s", linestyle="--", color="#8bc34a", linewidth=2,
        label=f"Proyeccion: {canonical}",
    )
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=4))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    ax.set_title(
        f"Predicta - Analisis y Proyeccion de Categoria: {canonical.upper()}",
        fontsize=13, fontweight="bold", pad=15,
    )
    ax.set_xlabel("Linea de Tiempo Operativa")
    ax.set_ylabel("Ventas Estimadas ($)")
    ax.grid(True, linestyle="--", alpha=0.6)
    plt.xticks(rotation=45)
    ax.legend(loc="upper left", fontsize=10)
    plt.tight_layout()
    chart_path = _save_fig_to_temp(fig)

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, txt=f"Predicta - Analisis de Categoria: {canonical.upper()}", ln=True, align="C")
    pdf.set_draw_color(0, 80, 180)
    pdf.line(10, 20, 200, 20)
    pdf.ln(5)
    pdf.image(chart_path, x=10, y=25, w=190)
    os.remove(chart_path)

    pdf.set_y(140)
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, txt="Desglose Mensual Operativo (Proyeccion)", ln=True, align="L")
    pdf.ln(2)
    pdf.set_fill_color(240, 240, 240)
    pdf.set_font("Arial", "B", 11)
    pdf.cell(90, 10, "Periodo Evaluado", 1, 0, "C", 1)
    pdf.cell(90, 10, "Proyeccion de Ingresos", 1, 1, "C", 1)
    pdf.set_font("Arial", "", 11)
    for label, amount in zip(future_labels, predictions, strict=False):
        pdf.cell(90, 10, label, 1, 0, "C")
        pdf.cell(90, 10, f"${amount:,.2f}", 1, 1, "C")

    pdf.set_font("Arial", "B", 11)
    pdf.set_fill_color(220, 230, 240)
    pdf.cell(90, 10, "TOTAL ESTIMADO (12 MESES)", 1, 0, "C", 1)
    pdf.cell(90, 10, f"${sum(predictions):,.2f}", 1, 1, "C", 1)

    return _build_pdf_response(pdf, filename=f"Predicta_{cat_key}_Proyeccion.pdf")
