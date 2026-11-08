// Plain-language wording for the monthly forecast metrics. Every new metric
// gets a title, a sentence built from its real value, and an explanation here.
import type { BaselineName, ValidationMetrics } from "../types/forecast";
import { formatCurrency, formatDecimal, formatNumber, formatPercent } from "./formatters";

export type MetricMeasure = "monto" | "cantidad";

export type MetricKey = "mape" | "rmse" | "r2" | "mejora";

export interface MetricExplanation {
  /** Plain title shown first. */
  title: string;
  /** Technical acronym, shown as secondary data. */
  acronym: string;
  /** What the metric means, for the info hint. */
  explanation: string;
  /** Sentence with the real value, or why the value is missing. */
  sentence: string;
  available: boolean;
}

export const METRIC_KEYS: readonly MetricKey[] = ["mape", "rmse", "r2", "mejora"];

const TITLES: Record<MetricKey, { title: string; acronym: string; explanation: string }> = {
  mape: {
    title: "Error promedio",
    acronym: "MAPE",
    explanation: "Cuánto se equivoca el modelo en promedio, en porcentaje del valor real. Menos es mejor.",
  },
  rmse: {
    title: "Margen típico",
    acronym: "RMSE",
    explanation:
      "El tamaño habitual del error, en dinero o en unidades. Penaliza más los errores grandes que los pequeños. Menos es mejor.",
  },
  r2: {
    title: "Patrón explicado",
    acronym: "R²",
    explanation:
      "Cuánto de la subida y bajada de las ventas entre los meses evaluados captura el modelo. Si es negativo, rinde peor que usar el promedio de esos meses.",
  },
  mejora: {
    title: "Frente a un cálculo simple",
    acronym: "Mejora vs. referencia",
    explanation:
      "Compara el error total del modelo con el del mejor cálculo simple (repetir el mes anterior, el mismo mes del año anterior o el promedio de 3 meses) sobre los mismos meses.",
  },
};

export const BASELINE_NAMES: Record<BaselineName, string> = {
  ultimo_valor: "repetir las ventas del mes anterior",
  mismo_mes_anio_anterior: "repetir el mismo mes del año anterior",
  promedio_movil_3: "usar el promedio de los últimos 3 meses",
};

/** Formats an error measured in the series' own unit. */
export function formatMeasureValue(measure: MetricMeasure, value: number): string {
  return measure === "monto" ? formatCurrency(value) : `${formatNumber(value)} unidades`;
}

function roundedPercent(value: number): string {
  return `${formatNumber(Math.round(Math.abs(value)))}%`;
}

/** Why a metric is null: never shown as zero. */
function unavailableReason(key: MetricKey, metrics: ValidationMetrics): string {
  if (metrics.origenes === 0) {
    return "Tu historial todavía no deja meses para comprobar el modelo.";
  }
  switch (key) {
    case "mape":
      return "Los meses evaluados no tuvieron ventas, así que no hay un porcentaje que calcular.";
    case "rmse":
      return "No hubo meses evaluados con los que medir el error.";
    case "r2":
      return metrics.origenes === 1
        ? "Hace falta comparar al menos dos meses evaluados."
        : "Las ventas de los meses evaluados no variaron, así que no hay cambios que explicar.";
    case "mejora":
      return "Ningún cálculo simple pudo estimar todos los meses evaluados para compararse.";
  }
}

function sentenceFor(key: MetricKey, value: number, measure: MetricMeasure, metrics: ValidationMetrics): string {
  switch (key) {
    case "mape":
      return value === 0
        ? "No se desvió del valor real en los meses evaluados."
        : `Se desvía en promedio un ${formatPercent(value)} del valor real.`;
    case "rmse":
      return value === 0
        ? "No tuvo error en los meses evaluados."
        : `Suele fallar por unos ${formatMeasureValue(measure, value)}.`;
    case "r2":
      if (value < 0) return "Rinde peor que usar el promedio de los meses evaluados.";
      if (value === 0) return "No explica los cambios en las ventas: rinde igual que usar el promedio.";
      return `Explica cerca del ${roundedPercent(value * 100)} de los cambios en las ventas de los meses evaluados.`;
    case "mejora": {
      const baseline = metrics.referencia ? BASELINE_NAMES[metrics.referencia] : "el mejor cálculo simple";
      if (value === 0) return `Se equivoca lo mismo que ${baseline}.`;
      return value > 0
        ? `Se equivoca ${roundedPercent(value)} menos que ${baseline}.`
        : `Se equivoca ${roundedPercent(value)} más que ${baseline}.`;
    }
  }
}

function rawValue(key: MetricKey, metrics: ValidationMetrics): number | null {
  return key === "mejora" ? metrics.mejora_vs_referencia : metrics[key];
}

export function explainMetric(key: MetricKey, metrics: ValidationMetrics, measure: MetricMeasure): MetricExplanation {
  const value = rawValue(key, metrics);
  const base = TITLES[key];
  if (value === null) {
    return { ...base, sentence: `No disponible. ${unavailableReason(key, metrics)}`, available: false };
  }
  return { ...base, sentence: sentenceFor(key, value, measure, metrics), available: true };
}

export type QualityLabel = "Muy buena" | "Buena" | "Aceptable" | "Baja";

/** Orientative label from the average error: <10 %, 10–20 %, 20–50 %, >50 %. */
export function qualityLabel(mape: number | null): QualityLabel | null {
  if (mape === null) return null;
  if (mape < 10) return "Muy buena";
  if (mape < 20) return "Buena";
  if (mape <= 50) return "Aceptable";
  return "Baja";
}

const MEASURE_NAMES: Record<MetricMeasure, string> = { monto: "el monto", cantidad: "la cantidad" };

/** One sentence that sums up the quality of one measure. */
export function qualitySummary(metrics: ValidationMetrics, measure: MetricMeasure): string {
  const { mape } = metrics;
  if (mape === null) {
    return `Aún no se puede calificar ${MEASURE_NAMES[measure]}. ${unavailableReason("mape", metrics)}`;
  }
  const label = qualityLabel(mape) ?? "";
  const months = metrics.origenes === 1 ? "el último mes evaluado" : `los últimos ${metrics.origenes} meses evaluados`;
  return `Calidad ${label.toLowerCase()}: en ${months}, ${MEASURE_NAMES[measure]} se desvió en promedio un ${formatPercent(mape)} del valor real.`;
}

export interface TechnicalRow {
  acronym: string;
  value: string;
}

/** Raw values for the "Detalle técnico" block, each with its unit. */
export function technicalRows(metrics: ValidationMetrics, measure: MetricMeasure): TechnicalRow[] {
  const show = (value: number | null, format: (value: number) => string) => (value === null ? "No disponible" : format(value));
  return [
    { acronym: "R²", value: show(metrics.r2, formatDecimal) },
    { acronym: "MAPE", value: show(metrics.mape, formatPercent) },
    { acronym: "RMSE", value: show(metrics.rmse, (value) => formatMeasureValue(measure, value)) },
    { acronym: "WAPE", value: show(metrics.wape, formatPercent) },
    { acronym: "MASE", value: show(metrics.mase, formatDecimal) },
    { acronym: "Meses evaluados", value: formatNumber(metrics.origenes) },
  ];
}
