// Chart-ready series for a monthly forecast. Every period comes from the
// backend: history, the incomplete month, and the projected months. Nothing is
// computed or filled in here; a value the backend did not send stays null.
import type { MonthlyForecastResponse } from "../../types/forecast";

export type ForecastMeasure = "monto" | "cantidad";

export const FORECAST_MEASURES: Record<ForecastMeasure, string> = {
  monto: "Monto",
  cantidad: "Cantidad",
};

/** History shown before the projection, so long histories do not squeeze it. */
export const HISTORY_MONTHS = 24;

export interface ForecastChartData {
  /** YYYY-MM periods, oldest first. */
  periodos: string[];
  historial: (number | null)[];
  parcial: (number | null)[];
  /** Starts at the last complete month so the dashed line continues the solid one. */
  proyeccion: (number | null)[];
  inferior: (number | null)[];
  superior: (number | null)[];
  extrapolacion: boolean[];
  /** Index in `periodos` of each projected month, in order. */
  indiceProyeccion: number[];
}

export function forecastChartData(
  forecast: MonthlyForecastResponse,
  measure: ForecastMeasure,
  historyMonths = HISTORY_MONTHS,
): ForecastChartData {
  const history = forecast.historial.slice(-historyMonths);
  const periods = history.map((month) => month.periodo);
  const size = () => periods.length;
  const empty = () => Array<number | null>(size()).fill(null);

  // The incomplete month is projected too, so it shares the first projected period.
  const projected = forecast.proyeccion.map((month) => month.periodo);
  for (const period of projected) if (!periods.includes(period)) periods.push(period);

  const data: ForecastChartData = {
    periodos: periods,
    historial: empty(),
    parcial: empty(),
    proyeccion: empty(),
    inferior: empty(),
    superior: empty(),
    extrapolacion: Array<boolean>(size()).fill(false),
    indiceProyeccion: [],
  };
  history.forEach((month, index) => {
    data.historial[index] = month[measure];
  });
  if (history.length) data.proyeccion[history.length - 1] = history[history.length - 1][measure];
  if (forecast.mes_parcial) {
    data.parcial[periods.indexOf(forecast.mes_parcial.periodo)] = forecast.mes_parcial[measure];
  }
  for (const month of forecast.proyeccion) {
    const index = periods.indexOf(month.periodo);
    data.proyeccion[index] = month[measure].prediccion;
    data.inferior[index] = month[measure].inferior;
    data.superior[index] = month[measure].superior;
    data.extrapolacion[index] = month.extrapolacion;
    data.indiceProyeccion.push(index);
  }
  return data;
}
