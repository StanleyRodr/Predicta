"""Excel and PDF reports with their charts.

Charts are built on ``matplotlib.figure.Figure`` objects and rendered to memory.
pyplot's global "current figure" is never used, so concurrent requests on
FastAPI's threadpool cannot draw on each other's charts, and no temporary file
is left behind when a report fails.
"""

import io
from dataclasses import dataclass
from datetime import date
from typing import Literal

import matplotlib
import pandas as pd
from fpdf import FPDF
from fpdf.enums import XPos, YPos
from matplotlib import dates as mdates
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.ticker import FuncFormatter
from sqlalchemy.orm import Session

from app.ml_models.forecast import monthly_aggregates, monthly_forecast
from app.services import analytics_service
from app.services.category_service import normalize_category
from app.services.formatting import EXCEL_MONEY_FORMAT, format_axis_money, format_money

# Figures are built without pyplot; Agg also keeps any indirect pyplot use headless.
matplotlib.use("Agg")

PDF_MEDIA_TYPE = "application/pdf"
EXCEL_MEDIA_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

MONTH_NAMES = [
    "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre",
]

# Aliases accepted by the monthly report endpoint (URL-friendly).
MONTH_ALIASES: dict[str, int] = {name.lower(): idx + 1 for idx, name in enumerate(MONTH_NAMES)}

# Bounds of the history PDF, which summarizes instead of listing every sale.
HISTORY_TOP_CATEGORIES = 15
HISTORY_MONTHS = 12
HISTORY_TOP_SALES = 20


class ReportError(Exception):
    """A report cannot be built; ``detail`` is safe to show to the user."""

    def __init__(self, status_code: int, detail: str) -> None:
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


@dataclass(frozen=True)
class Report:
    content: bytes
    filename: str
    media_type: str = PDF_MEDIA_TYPE


# =====================================================================
# Chart and PDF helpers
# =====================================================================


class _PDFReport(FPDF):
    """FPDF subclass with Predicta branding (header + footer)."""

    def header(self) -> None:
        self.set_font("helvetica", "B", 15)
        self.cell(0, 10, "Predicta - Reporte", align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_draw_color(0, 80, 180)
        self.line(10, 22, 200, 22)
        self.ln(10)

    def footer(self) -> None:
        self.set_y(-15)
        self.set_font("helvetica", "I", 8)
        self.cell(0, 10, f"Página {self.page_no()}", align="C")


def _new_fig(*, figsize: tuple[float, float] = (8, 4)) -> tuple[Figure, Axes]:
    """Return a figure detached from pyplot's global state, so threads never share it."""
    fig = Figure(figsize=figsize)
    return fig, fig.subplots()


def _rotate_x_labels(
    ax: Axes, rotation: float, ha: Literal["left", "center", "right"] = "center"
) -> None:
    for label in ax.get_xticklabels():
        label.set_rotation(rotation)
        label.set_horizontalalignment(ha)


def use_money_axis(ax: Axes) -> None:
    """Show the vertical axis with comma thousands."""
    ax.yaxis.set_major_formatter(
        FuncFormatter(lambda value, _position: format_axis_money(value))
    )


def _render_png(fig: Figure, *, dpi: int = 150) -> io.BytesIO:
    """Render a figure to an in-memory PNG."""
    buffer = io.BytesIO()
    fig.savefig(buffer, format="png", dpi=dpi, bbox_inches="tight")
    buffer.seek(0)
    return buffer


def _pdf_bytes(pdf: FPDF) -> bytes:
    return bytes(pdf.output())


def _monthly_history(
    db: Session,
    user_id: int,
    *,
    categoria: str | None = None,
    no_data: str,
    too_short: str,
) -> tuple[list[analytics_service.DailySales], pd.DataFrame]:
    """Return daily totals and their monthly roll-up, or explain why there are none."""
    daily = analytics_service.daily_sales(db, user_id, categoria)
    if not daily:
        raise ReportError(400, no_data)
    monthly = monthly_aggregates(daily)
    if len(monthly) < 2:
        raise ReportError(400, too_short)
    return daily, monthly


# =====================================================================
# Excel & basic PDF reports
# =====================================================================


def sales_excel(db: Session, user_id: int, username: str) -> Report:
    """Return the user's full sales history as an .xlsx file."""
    ventas = analytics_service.sales_for_export(db, user_id)
    if not ventas:
        raise ReportError(404, "No hay datos para exportar.")

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
        worksheet = writer.sheets["Historial de Ventas"]
        amount_column = df.columns.get_loc("Monto") + 1
        for (cell,) in worksheet.iter_rows(
            min_row=2, min_col=amount_column, max_col=amount_column
        ):
            cell.number_format = EXCEL_MONEY_FORMAT

    return Report(
        content=output.getvalue(),
        filename=f"Reporte_Ventas_{username}.xlsx",
        media_type=EXCEL_MEDIA_TYPE,
    )


def _table(
    pdf: FPDF,
    headers: list[str],
    widths: list[float],
    rows: list[list[str]],
    *,
    right_aligned: frozenset[int] = frozenset(),
) -> None:
    """Draw a bordered table whose header repeats after each page break."""

    def draw_header() -> None:
        pdf.set_fill_color(230, 230, 230)
        pdf.set_font("helvetica", "B", 10)
        for width, header in zip(widths, headers, strict=True):
            pdf.cell(width, 8, header, 1, align="C", fill=True)
        pdf.ln()
        pdf.set_font("helvetica", size=10)

    draw_header()
    for row in rows:
        if pdf.will_page_break(8):
            pdf.add_page()
            draw_header()
        for index, (width, value) in enumerate(zip(widths, row, strict=True)):
            pdf.cell(width, 8, value, 1, align="R" if index in right_aligned else "L")
        pdf.ln()


def _section_title(pdf: FPDF, title: str) -> None:
    if pdf.will_page_break(30):
        pdf.add_page()
    pdf.ln(4)
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(0, 8, title, new_x=XPos.LMARGIN, new_y=YPos.NEXT)


def _month_label(moment: date | pd.Timestamp) -> str:
    return f"{MONTH_NAMES[moment.month - 1]} {moment.year}"


def history_pdf(db: Session, user_id: int, username: str) -> Report:
    """Return a bounded historical summary: metrics, categories, months, top sales.

    The size depends on the number of categories shown, months shown, and top
    sales listed, never on how many sales the user has.
    """
    metrics = analytics_service.global_metrics(db, user_id)
    if not metrics["cantidad_operaciones"]:
        raise ReportError(404, "No hay datos para generar el reporte.")

    monthly = monthly_aggregates(analytics_service.daily_sales(db, user_id))
    categories = sorted(
        analytics_service.category_breakdown(db, user_id),
        key=lambda row: row["ingresos_totales"],
        reverse=True,
    )
    top_sales = analytics_service.top_sales(db, user_id, HISTORY_TOP_SALES)

    fig, ax = _new_fig()
    ax.plot(
        monthly["fecha"],
        monthly["monto"],
        marker="o",
        linestyle="-",
        color="#0050b3",
        linewidth=2,
    )
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    ax.set_title("Evolución de Ventas Mensuales", fontsize=12)
    ax.set_ylabel("Monto de Ventas ($)")
    use_money_axis(ax)
    ax.grid(True, linestyle="--", alpha=0.5)
    _rotate_x_labels(ax, 45, "right")
    fig.tight_layout()
    chart = _render_png(fig)

    pdf = _PDFReport()
    pdf.add_page()
    pdf.image(chart, x=15, y=30, w=180)
    pdf.set_y(125)

    _section_title(pdf, "Métricas globales")
    _table(
        pdf,
        ["Indicador", "Valor"],
        [110, 80],
        [
            ["Ingresos totales", format_money(metrics["total_ingresos"])],
            ["Operaciones", f"{metrics['cantidad_operaciones']:,}"],
            ["Ticket promedio", format_money(metrics["ticket_promedio"])],
            ["Venta más alta", format_money(metrics["venta_mas_alta"])],
        ],
        right_aligned=frozenset({1}),
    )

    shown = categories[:HISTORY_TOP_CATEGORIES]
    category_rows = [
        [
            str(row["categoria"] or "Sin categoría")[:40],
            format_money(row["ingresos_totales"]),
            f"{row['cantidad_ventas']:,}",
            format_money(row["ticket_promedio"]),
        ]
        for row in shown
    ]
    rest = categories[HISTORY_TOP_CATEGORIES:]
    if rest:
        revenue = sum(row["ingresos_totales"] for row in rest)
        count = sum(row["cantidad_ventas"] for row in rest)
        category_rows.append(
            [
                f"Otras ({len(rest)} categorías)",
                format_money(revenue),
                f"{count:,}",
                format_money(round(revenue / count, 2)),
            ]
        )
    _section_title(pdf, "Ventas por categoría")
    _table(
        pdf,
        ["Categoría", "Ingresos", "Ventas", "Ticket promedio"],
        [70, 45, 30, 45],
        category_rows,
        right_aligned=frozenset({1, 2, 3}),
    )

    _section_title(pdf, f"Últimos {HISTORY_MONTHS} meses con ventas")
    _table(
        pdf,
        ["Mes", "Ingresos", "Unidades"],
        [80, 60, 50],
        [
            [_month_label(row.fecha), format_money(row.monto), f"{row.cantidad:,.2f}"]
            for row in monthly.tail(HISTORY_MONTHS).itertuples()
        ],
        right_aligned=frozenset({1, 2}),
    )

    _section_title(pdf, f"Las {HISTORY_TOP_SALES} ventas de mayor monto")
    _table(
        pdf,
        ["Producto", "Categoría", "Fecha", "Monto"],
        [70, 50, 30, 40],
        [
            [
                sale.producto[:34],
                str(sale.categoria or "Sin categoría")[:24],
                sale.fecha_venta.strftime("%d/%m/%Y"),
                format_money(sale.monto),
            ]
            for sale in top_sales
        ],
        right_aligned=frozenset({3}),
    )

    return Report(content=_pdf_bytes(pdf), filename=f"Reporte_Predicta_{username}.pdf")


# =====================================================================
# Annual forecast report
# =====================================================================


def annual_forecast_pdf(db: Session, user_id: int, username: str) -> Report:
    """Return a PDF with the next-12-month forecast combined with history."""
    daily, monthly = _monthly_history(
        db,
        user_id,
        no_data="No hay datos historicos para procesar.",
        too_short="Muestreo insuficiente para analisis lineal.",
    )
    _, future_dates, predictions = monthly_forecast(daily)

    last_date = monthly["fecha"].max()
    last_amount = float(monthly.iloc[-1]["monto"])

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
        label="Proyección Estimada (Próximos 12 meses)",
    )
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=6))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    ax.set_title(
        "Predicta - Historial y Proyección de la Demanda Global",
        fontsize=14, fontweight="bold", pad=15,
    )
    ax.set_xlabel("Línea de Tiempo Operativa")
    ax.set_ylabel("Ingresos ($)")
    use_money_axis(ax)
    ax.grid(True, linestyle="--", alpha=0.5)
    _rotate_x_labels(ax, 45)
    ax.legend(loc="upper left", fontsize=10)
    fig.tight_layout()
    chart = _render_png(fig)

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("helvetica", "B", 16)
    pdf.cell(
        0, 10, text="Predicta - Planificación y Proyección de la Demanda",
        align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT,
    )
    pdf.set_draw_color(0, 80, 180)
    pdf.line(10, 20, 200, 20)
    pdf.ln(10)
    pdf.set_font("helvetica", size=12)
    pdf.cell(
        0, 10,
        text=f"Ingreso Acumulado Estimado (Próximos 12 meses): {format_money(sum(predictions))}",
        new_x=XPos.LMARGIN, new_y=YPos.NEXT,
    )
    pdf.ln(5)
    pdf.image(chart, x=10, y=45, w=190)

    return Report(
        content=_pdf_bytes(pdf), filename=f"Predicta_Reporte_Anual_{username}.pdf"
    )


# =====================================================================
# Monthly report (by name)
# =====================================================================


def comparison_labels(
    history: list[pd.Timestamp], projection: pd.Timestamp
) -> list[str]:
    """Label each past occurrence of a month by its year, then the projection.

    Each year holds the requested month at most once, so labels never repeat.
    """
    return [str(moment.year) for moment in history] + [f"{projection.year} (estimado)"]


def monthly_report_pdf(db: Session, user_id: int, mes: str) -> Report:
    """Return a PDF with bar comparison of a future month against history."""
    month_key = mes.lower().strip()
    if month_key not in MONTH_ALIASES:
        raise ReportError(400, f"El modulo analitico no reconoce el mes '{mes}'.")
    target_month = MONTH_ALIASES[month_key]

    daily, monthly = _monthly_history(
        db,
        user_id,
        no_data="Ecosistema sin registros para entrenamiento.",
        too_short="Varianza insuficiente para ejecutar regresion.",
    )

    _, future_dates, predictions = monthly_forecast(daily, horizon=12)
    projection_index = next(
        (index for index, current_date in enumerate(future_dates) if current_date.month == target_month),
        None,
    )
    if projection_index is None:
        raise ReportError(
            400, "El mes solicitado cae fuera del rango de prevision de 12 meses."
        )

    projection_date = future_dates[projection_index]
    monto_predicho = float(predictions[projection_index])

    historical = monthly[monthly["fecha"].dt.month == target_month]
    labels = comparison_labels(list(historical["fecha"]), projection_date)
    values = list(historical["monto"])
    values.append(monto_predicho)

    fig, ax = _new_fig(figsize=(8, 4.5))
    colors = ["#0050b3"] * (len(values) - 1) + ["#e65100"]
    bars = ax.bar(labels, values, color=colors, edgecolor="black", width=0.6)
    ax.set_title(
        f"Análisis Comparativo Interanual: Periodo {mes.upper()}",
        fontsize=12, fontweight="bold",
    )
    ax.set_ylabel("Volumen de Ingresos ($)")
    use_money_axis(ax)
    ax.grid(True, axis="y", linestyle="--", alpha=0.5)
    for bar in bars:
        ax.annotate(
            format_money(bar.get_height()),
            xy=(bar.get_x() + bar.get_width() / 2, bar.get_height()),
            xytext=(0, 3), textcoords="offset points",
            ha="center", va="bottom", fontsize=9,
        )
    fig.tight_layout()
    chart = _render_png(fig)

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("helvetica", "B", 15)
    pdf.cell(
        0, 10, text="Predicta - Diagnóstico Gráfico Mensual",
        align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT,
    )
    pdf.set_draw_color(0, 80, 180)
    pdf.line(10, 20, 200, 20)
    pdf.ln(15)
    pdf.image(chart, x=15, y=35, w=180)

    return Report(content=_pdf_bytes(pdf), filename=f"Predicta_Inferencia_{month_key}.pdf")


# =====================================================================
# Category forecast report
# =====================================================================


def category_forecast_pdf(db: Session, user_id: int, categoria: str) -> Report:
    """Return a PDF with the 12-month forecast filtered to a single category."""
    canonical = normalize_category(categoria)
    cat_key = canonical.lower().replace(" ", "-")

    daily, monthly = _monthly_history(
        db,
        user_id,
        categoria=canonical,
        no_data=f"No hay registros historicos para la categoria '{canonical}'.",
        too_short="Historial insuficiente para proyeccion lineal en esta categoria.",
    )
    _, future_dates, predictions = monthly_forecast(daily)

    last_date = monthly["fecha"].max()
    last_amount = float(monthly.iloc[-1]["monto"])
    future_labels = [f"{MONTH_NAMES[d.month - 1]} {d.year}" for d in future_dates]
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
        label=f"Proyección: {canonical}",
    )
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=4))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    ax.set_title(
        f"Predicta - Análisis y Proyección de Categoría: {canonical.upper()}",
        fontsize=13, fontweight="bold", pad=15,
    )
    ax.set_xlabel("Línea de Tiempo Operativa")
    ax.set_ylabel("Ventas Estimadas ($)")
    use_money_axis(ax)
    ax.grid(True, linestyle="--", alpha=0.6)
    _rotate_x_labels(ax, 45)
    ax.legend(loc="upper left", fontsize=10)
    fig.tight_layout()
    chart = _render_png(fig)

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("helvetica", "B", 16)
    pdf.cell(
        0, 10, text=f"Predicta - Análisis de Categoría: {canonical.upper()}",
        align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT,
    )
    pdf.set_draw_color(0, 80, 180)
    pdf.line(10, 20, 200, 20)
    pdf.ln(5)
    pdf.image(chart, x=10, y=25, w=190)

    pdf.set_y(140)
    pdf.set_font("helvetica", "B", 14)
    pdf.cell(
        0, 10, text="Desglose Mensual Operativo (Proyección)",
        align="L", new_x=XPos.LMARGIN, new_y=YPos.NEXT,
    )
    pdf.ln(2)
    pdf.set_fill_color(240, 240, 240)
    pdf.set_font("helvetica", "B", 11)
    pdf.cell(90, 10, "Periodo Evaluado", 1, align="C", fill=True)
    pdf.cell(90, 10, "Proyección de Ingresos", 1, align="C", fill=True, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("helvetica", "", 11)
    for label, amount in zip(future_labels, predictions, strict=False):
        pdf.cell(90, 10, label, 1, align="C")
        pdf.cell(90, 10, format_money(amount), 1, align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.set_font("helvetica", "B", 11)
    pdf.set_fill_color(220, 230, 240)
    pdf.cell(90, 10, "TOTAL ESTIMADO (12 MESES)", 1, align="C", fill=True)
    pdf.cell(90, 10, format_money(sum(predictions)), 1, align="C", fill=True, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    return Report(content=_pdf_bytes(pdf), filename=f"Predicta_{cat_key}_Proyeccion.pdf")
