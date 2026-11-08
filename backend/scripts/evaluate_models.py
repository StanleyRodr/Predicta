"""Evaluate the monthly forecast against simple baselines and a stronger model.

Reads the sample workbook, backtests every model with a rolling origin, and
writes the tables and charts of the thesis chapter to ``docs/evaluacion/``:

- rolling origin with 18 initial training months and horizons 1 to 6;
- the regression as the system applies it, and the seasonal specification
  forced at every origin;
- baselines: last value, same month a year earlier, 3-month moving average;
- damped-trend ETS, here only, never at runtime;
- WAPE, MASE, MAPE, RMSE, R², 95 % interval coverage, residual diagnostics;
- the tiered model cut to 6, 12, and 18 months, against what came after.

Every number comes from months the model did not see. Run from ``backend/``:

    python scripts/evaluate_models.py
"""

import sys
import warnings
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

import matplotlib

matplotlib.use("Agg")
import statsmodels.api as sm
from matplotlib.figure import Figure
from matplotlib.ticker import FuncFormatter
from statsmodels.stats.diagnostic import acorr_ljungbox, het_breuschpagan
from statsmodels.tsa.exponential_smoothing.ets import ETSModel

from app.ml_models.evaluation import (
    BASELINES,
    BacktestRecord,
    ModelFn,
    baseline_model,
    improvement,
    interval_coverage,
    point_metrics,
    rolling_origin,
    wape,
)
from app.ml_models.forecast import (
    applied_model,
    build_seasonal_features,
    forecast_from_sales,
    monthly_forecast_series,
    monthly_regression,
    months_elapsed,
)
from app.services.category_service import normalize_category
from app.services.formatting import format_axis_money

SEED = 20261108
WORKBOOK = ROOT / "DatosDePrueba" / "ventas_fabricadas" / "ventas_tienda_2_anios.xlsx"
OUTPUT = ROOT / "docs" / "evaluacion"
INITIAL = 18
HORIZONS = range(1, 7)
LEVELS = (6, 12, 18)
TARGET = "monto"

MODEL_LABELS = {
    "regla": "Regresión (regla aplicada)",
    "estacional_forzada": "Regresión estacional forzada",
    "ets_amortiguado": "ETS con tendencia amortiguada",
    "ultimo_valor": "Último valor",
    "mismo_mes_anio_anterior": "Mismo mes del año anterior",
    "promedio_movil_3": "Promedio móvil de 3 meses",
}
REGRESSIONS = ("regla", "estacional_forzada")


@dataclass(frozen=True)
class Sale:
    fecha_venta: date
    monto: float
    cantidad: float


# ---------------------------------------------------------------- data


def load_sales() -> pd.DataFrame:
    frame = pd.read_excel(WORKBOOK)
    frame.columns = [str(column).strip().lower() for column in frame.columns]
    frame["fecha"] = pd.to_datetime(frame["fecha"]).dt.date
    frame["categoria"] = frame["categoria"].map(normalize_category)
    if "cantidad" not in frame:
        frame["cantidad"] = 1.0
    return frame


def complete_months(rows: pd.DataFrame) -> pd.DataFrame:
    sales = [Sale(r.fecha, float(r.monto), float(r.cantidad)) for r in rows.itertuples()]
    return forecast_from_sales(sales).historial


# ---------------------------------------------------------------- models


def rule_model(train: pd.DataFrame, target: str, future_dates: list[pd.Timestamp]) -> pd.DataFrame | None:
    """The specification the system would pick for this many training months."""
    seasonal, _ = applied_model(len(train), train)
    return monthly_regression(seasonal)(train, target, future_dates)


def ets_model(train: pd.DataFrame, target: str, future_dates: list[pd.Timestamp]) -> pd.DataFrame | None:
    """Damped additive-trend ETS without seasonality, with 95 % prediction intervals."""
    values = train[target].to_numpy(dtype=float)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        fitted = ETSModel(pd.Series(values), error="add", trend="add", damped_trend=True).fit(disp=False)
        frame = fitted.get_prediction(start=len(values), end=len(values) + len(future_dates) - 1).summary_frame(
            alpha=0.05
        )
    return pd.DataFrame(
        {
            "mean": frame["mean"].clip(lower=0).to_numpy(),
            "lower": frame["pi_lower"].clip(lower=0).to_numpy(),
            "upper": frame["pi_upper"].clip(lower=0).to_numpy(),
        }
    )


def models() -> dict[str, ModelFn]:
    catalog: dict[str, ModelFn] = {
        "regla": rule_model,
        "estacional_forzada": monthly_regression(True),
        "ets_amortiguado": ets_model,
    }
    catalog.update({name: baseline_model(fn) for name, fn in BASELINES.items()})
    return catalog


# ---------------------------------------------------------------- backtest


def backtest(history: pd.DataFrame) -> dict[str, list[BacktestRecord]]:
    return {
        name: rolling_origin(history, TARGET, model, initial=INITIAL, horizons=HORIZONS)
        for name, model in models().items()
    }


def horizon_table(history: pd.DataFrame, records: dict[str, list[BacktestRecord]]) -> pd.DataFrame:
    training = history[TARGET].to_numpy(dtype=float)[:INITIAL]
    rows = []
    for name, model_records in records.items():
        for step in HORIZONS:
            subset = [r for r in model_records if r.horizonte == step and r.prediccion is not None]
            actual = np.array([r.real for r in subset])
            predicted = np.array([r.prediccion for r in subset], dtype=float)
            scores = point_metrics(actual, predicted, training)
            rows.append(
                {
                    "modelo": name,
                    "horizonte": step,
                    "n": len(subset),
                    **scores,
                    "cobertura_95": interval_coverage(subset),
                }
            )
    return pd.DataFrame(rows)


def improvement_table(table: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for step in HORIZONS:
        at_step = table[table["horizonte"] == step].set_index("modelo")
        baselines = at_step.loc[list(BASELINES)]["wape"].dropna()
        best = baselines.idxmin() if len(baselines) else None
        for name in REGRESSIONS:
            rows.append(
                {
                    "horizonte": step,
                    "modelo": name,
                    "wape_modelo": at_step.loc[name, "wape"],
                    "mejor_referencia": best,
                    "wape_referencia": baselines.min() if best else None,
                    "mejora_pct": improvement(at_step.loc[name, "wape"], baselines.min() if best else None),
                    "gana_a_estacional_ingenuo": _beats(at_step, name, "mismo_mes_anio_anterior"),
                }
            )
    return pd.DataFrame(rows)


def _beats(at_step: pd.DataFrame, name: str, baseline: str) -> bool | None:
    model_error, baseline_error = at_step.loc[name, "wape"], at_step.loc[baseline, "wape"]
    if pd.isna(model_error) or pd.isna(baseline_error):
        return None
    return bool(model_error < baseline_error)


def residual_diagnostics(history: pd.DataFrame) -> dict[str, float]:
    """Ljung-Box and Breusch-Pagan on the residuals of the final 24-month fit."""
    seasonal, _ = applied_model(len(history), history)
    index = months_elapsed(history["fecha"])
    design = (
        build_seasonal_features(index, history["fecha"].dt.month)
        if seasonal
        else pd.DataFrame({"mes_indice": index.astype(float)})
    )
    exog = sm.add_constant(design, has_constant="add")
    fitted = sm.OLS(history[TARGET].to_numpy(dtype=float), exog).fit()
    box = acorr_ljungbox(fitted.resid, lags=[3, 6], return_df=True)
    _, bp_pvalue, _, _ = het_breuschpagan(fitted.resid, exog)
    return {
        "modelo": "tendencia_estacional" if seasonal else "tendencia",
        "ljung_box_p_lag3": float(box.loc[3, "lb_pvalue"]),
        "ljung_box_p_lag6": float(box.loc[6, "lb_pvalue"]),
        "breusch_pagan_p": float(bp_pvalue),
    }


# ---------------------------------------------------------------- tiered levels


def level_table(history: pd.DataFrame) -> tuple[pd.DataFrame, dict[int, tuple]]:
    """Cut the history to 6, 12, and 18 months, project, and compare with what came after."""
    rows, charts = [], {}
    for months in LEVELS:
        cut = history.iloc[:months].reset_index(drop=True)
        after = history.iloc[months:].reset_index(drop=True)
        forecast = monthly_forecast_series(cut, cut["fecha"].iloc[-1].date())
        points = forecast.objetivos[TARGET].puntos[: len(after)]
        actual = after[TARGET].to_numpy(dtype=float)[: len(points)]
        predicted = np.array([p.prediccion for p in points])
        records = [
            BacktestRecord(months, step, p.fecha, float(real), p.prediccion, p.inferior, p.superior)
            for step, (p, real) in enumerate(zip(points, actual, strict=True), start=1)
        ]
        naive = np.array([BASELINES["ultimo_valor"](cut, TARGET, p.fecha) for p in points], dtype=float)
        seasonal = [BASELINES["mismo_mes_anio_anterior"](cut, TARGET, p.fecha) for p in points]
        rows.append(
            {
                "meses_de_historial": months,
                "modelo": forecast.modelo,
                "horizonte": forecast.horizonte,
                "meses_comparados": len(points),
                "wape": wape(actual, predicted),
                "mape": point_metrics(actual, predicted, cut[TARGET].to_numpy(dtype=float))["mape"],
                "cobertura_95": interval_coverage(records),
                "wape_ultimo_valor": wape(actual, naive),
                "wape_mismo_mes_anio_anterior": None
                if any(v is None for v in seasonal)
                else wape(actual, np.array(seasonal, dtype=float)),
            }
        )
        charts[months] = (cut, after, points, forecast.modelo)
    return pd.DataFrame(rows), charts


# ---------------------------------------------------------------- categories


def category_table(sales: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for name, group in sales.groupby("categoria"):
        history = complete_months(group)
        table = horizon_table(history, backtest(history))
        mean_wape = table.groupby("modelo")["wape"].mean()
        best = mean_wape.loc[list(BASELINES)].idxmin()
        rows.append(
            {
                "categoria": name,
                "wape_regla": mean_wape["regla"],
                "wape_estacional_forzada": mean_wape["estacional_forzada"],
                "wape_ets": mean_wape["ets_amortiguado"],
                "mejor_referencia": best,
                "wape_referencia": mean_wape[best],
                "mejora_regla_pct": improvement(mean_wape["regla"], mean_wape[best]),
            }
        )
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- output


def _number(value, digits=2) -> str:
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return "—"
    if isinstance(value, bool | np.bool_):
        return "sí" if value else "no"
    if isinstance(value, int | np.integer):
        return f"{value:,}"
    if isinstance(value, float | np.floating):
        return f"{value:,.{digits}f}"
    return MODEL_LABELS.get(str(value), str(value))


def markdown(table: pd.DataFrame, headers: dict[str, str]) -> str:
    lines = ["| " + " | ".join(headers.values()) + " |", "|" + "---|" * len(headers)]
    for row in table.itertuples(index=False):
        values = row._asdict()
        lines.append("| " + " | ".join(_number(values[key]) for key in headers) + " |")
    return "\n".join(lines)


def error_chart(table: pd.DataFrame, path: Path) -> None:
    fig = Figure(figsize=(9, 5))
    ax = fig.subplots()
    colors = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#6250d6"]
    for color, name in zip(colors, MODEL_LABELS, strict=True):
        subset = table[table["modelo"] == name]
        style = "-" if name in REGRESSIONS or name == "ets_amortiguado" else "--"
        ax.plot(subset["horizonte"], subset["wape"], style, marker="o", color=color, linewidth=2, label=MODEL_LABELS[name])
    ax.set_xlabel("Meses hacia adelante")
    ax.set_ylabel("WAPE (%)")
    ax.set_title("Error por horizonte en el backtest (menor es mejor)")
    ax.set_xticks(list(HORIZONS))
    ax.grid(True, linestyle="--", alpha=0.4)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=150, metadata={"Software": None})


def levels_chart(charts: dict[int, tuple], path: Path) -> None:
    fig = Figure(figsize=(12, 3.8))
    axes = fig.subplots(1, len(charts), sharey=True)
    for ax, (months, (cut, after, points, model)) in zip(axes, charts.items(), strict=True):
        ax.plot(cut["fecha"], cut[TARGET], marker="o", color="#2a78d6", linewidth=1.5, label="Historial usado")
        ax.plot(after["fecha"], after[TARGET], marker="o", color="#8b949e", linewidth=1.5, label="Lo que ocurrió")
        dates = [p.fecha for p in points]
        ax.plot(dates, [p.prediccion for p in points], "--", marker="s", color="#eb6834", linewidth=1.5, label="Proyección")
        ax.fill_between(dates, [p.inferior for p in points], [p.superior for p in points], color="#eb6834", alpha=0.18, linewidth=0)
        ax.set_title(f"{months} meses: {model.replace('_', ' ')}", fontsize=10)
        ax.tick_params(axis="x", labelrotation=45, labelsize=7)
        ax.grid(True, linestyle="--", alpha=0.4)
    axes[0].set_ylabel("Ingresos ($)")
    axes[0].yaxis.set_major_formatter(FuncFormatter(lambda value, _position: format_axis_money(value)))
    axes[0].legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(path, dpi=150, metadata={"Software": None})


def main() -> None:
    np.random.seed(SEED)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    sales = load_sales()
    history = complete_months(sales)

    records = backtest(history)
    by_horizon = horizon_table(history, records)
    gains = improvement_table(by_horizon)
    diagnostics = residual_diagnostics(history)
    levels, level_charts = level_table(history)
    categories = category_table(sales)

    for name, frame in {
        "backtest_por_horizonte": by_horizon,
        "mejora_vs_referencia": gains,
        "niveles_escalonados": levels,
        "categorias": categories,
    }.items():
        frame.round(4).to_csv(OUTPUT / f"{name}.csv", index=False)
    pd.DataFrame([diagnostics]).round(4).to_csv(OUTPUT / "diagnostico_residuos.csv", index=False)
    error_chart(by_horizon, OUTPUT / "error_por_horizonte.png")
    levels_chart(level_charts, OUTPUT / "niveles_escalonados.png")

    losses = {
        # None (not comparable) is not a loss.
        name: sum(won is False for won in gains[gains["modelo"] == name]["gana_a_estacional_ingenuo"])
        for name in REGRESSIONS
    }
    wide = by_horizon.pivot(index="horizonte", columns="modelo", values="wape").reset_index()
    report = f"""# Evaluación de los modelos de proyección

Generado por `backend/scripts/evaluate_models.py` (semilla {SEED}) con
`{WORKBOOK.relative_to(ROOT).as_posix()}`: {len(sales):,} ventas, {len(history)} meses
completos, de {history['fecha'].min():%Y-%m} a {history['fecha'].max():%Y-%m}. Todas
las métricas salen de meses que el modelo no vio. Los datos son fabricados: muestran
que el método funciona, no su desempeño en una tienda real.

## Backtest con origen móvil

Se entrena con los primeros {INITIAL} meses y se avanza un mes por vez; en cada origen
se predicen los meses 1 a 6 siguientes. El horizonte 1 tiene 6 orígenes y el 6, uno
solo. Con 24 meses no se pueden validar los meses 7 a 12: son extrapolación sin
validar.

"Regla aplicada" es lo que el sistema hace con ese historial: con 18 a 23 meses, solo
tendencia. "Estacional forzada" ajusta tendencia y 11 meses del calendario aunque el
sistema no la use con ese historial. Con 18 a 23 meses cada mes del calendario tiene
1 o 2 observaciones, así que esta evaluación es débil.

Este backtest motivó la regla actual: la especificación estacional, que antes se
usaba desde 24 meses, perdía contra el mismo mes del año anterior en la mayoría de
los horizontes. Desde entonces la estacionalidad empieza en 36 meses (3 observaciones
por mes del calendario) y con 24 a 35 meses se usa solo la tendencia.

### WAPE (%) por horizonte

{markdown(wide, {"horizonte": "Horizonte", **{name: MODEL_LABELS[name] for name in MODEL_LABELS}})}

![Error por horizonte](error_por_horizonte.png)

### Mejora frente al mejor modelo de referencia

Mejora porcentual del WAPE frente al mejor de los tres modelos simples en cada
horizonte. Un valor negativo significa que la regresión pierde.

{markdown(gains, {"horizonte": "Horizonte", "modelo": "Modelo", "wape_modelo": "WAPE modelo", "mejor_referencia": "Mejor referencia", "wape_referencia": "WAPE referencia", "mejora_pct": "Mejora (%)", "gana_a_estacional_ingenuo": "Gana al mismo mes del año anterior"})}

La regla aplicada pierde contra el mismo mes del año anterior en
{losses["regla"]} de 6 horizontes; la estacional forzada, en {losses["estacional_forzada"]} de 6.

### Detalle por modelo y horizonte

{markdown(by_horizon, {"modelo": "Modelo", "horizonte": "Horizonte", "n": "n", "wape": "WAPE", "mase": "MASE", "mape": "MAPE", "rmse": "RMSE", "r2": "R²", "cobertura_95": "Cobertura 95 %"})}

MASE se escala con el error del último valor dentro de los {INITIAL} meses iniciales:
menor que 1 es mejor que ese modelo ingenuo. R² con 1 a 6 puntos es inestable y se
muestra solo para completar. La cobertura es el porcentaje de meses reales dentro del
intervalo del 95 %; los modelos simples no tienen intervalo.

## Diagnóstico de residuos

Modelo final con los {len(history)} meses: {diagnostics["modelo"].replace("_", " ")}.

| Prueba | Valor p |
|---|---|
| Ljung–Box, 3 rezagos | {_number(diagnostics["ljung_box_p_lag3"], 4)} |
| Ljung–Box, 6 rezagos | {_number(diagnostics["ljung_box_p_lag6"], 4)} |
| Breusch–Pagan | {_number(diagnostics["breusch_pagan_p"], 4)} |

Un valor p menor que 0.05 en Ljung–Box indica autocorrelación en los residuos; en
Breusch–Pagan, varianza no constante.

## Niveles del modelo escalonado

El historial se corta a 6, 12 y 18 meses, se proyecta con la regla del sistema y se
compara con lo que ocurrió después.

{markdown(levels, {"meses_de_historial": "Meses usados", "modelo": "Modelo", "horizonte": "Horizonte", "meses_comparados": "Meses comparados", "wape": "WAPE", "mape": "MAPE", "cobertura_95": "Cobertura 95 %", "wape_ultimo_valor": "WAPE último valor", "wape_mismo_mes_anio_anterior": "WAPE mismo mes año anterior"})}

![Niveles del modelo escalonado](niveles_escalonados.png)

## Por categoría

WAPE promedio de los horizontes 1 a 6 en el backtest de cada categoría.

{markdown(categories, {"categoria": "Categoría", "wape_regla": "Regla aplicada", "wape_estacional_forzada": "Estacional forzada", "wape_ets": "ETS amortiguado", "mejor_referencia": "Mejor referencia", "wape_referencia": "WAPE referencia", "mejora_regla_pct": "Mejora regla (%)"})}
"""
    (OUTPUT / "resultados.md").write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
