// Turn backend series points into chart-ready values. Periods the backend did not
// return have no sales: they become null (a gap in the line), never zero.
import type { Measure, SeriesPoint } from "../types/analytics";

export const MONTH_LABELS = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"];

export const MONTH_NAMES = [
  "Enero",
  "Febrero",
  "Marzo",
  "Abril",
  "Mayo",
  "Junio",
  "Julio",
  "Agosto",
  "Septiembre",
  "Octubre",
  "Noviembre",
  "Diciembre",
];

export interface ValueSeries<Key> {
  key: Key;
  values: (number | null)[];
}

export interface ChartSeries<Key> {
  labels: string[];
  series: ValueSeries<Key>[];
}

/** One line per year over a January-to-December axis. */
export function yearOverlayData(points: SeriesPoint[], measure: Measure): ChartSeries<number> {
  const byYear = new Map<number, (number | null)[]>();
  for (const point of points) {
    const values = byYear.get(point.anio) ?? Array<number | null>(12).fill(null);
    values[point.mes - 1] = point[measure];
    byYear.set(point.anio, values);
  }
  return {
    labels: MONTH_LABELS,
    series: [...byYear.entries()].sort(([a], [b]) => a - b).map(([key, values]) => ({ key, values })),
  };
}

/** Every month from the first to the last observed one, as YYYY-MM. */
export function monthRange(points: SeriesPoint[]): string[] {
  if (!points.length) return [];
  const indexes = points.map((point) => point.anio * 12 + point.mes - 1);
  const first = Math.min(...indexes);
  const last = Math.max(...indexes);
  const months: string[] = [];
  for (let index = first; index <= last; index += 1) {
    months.push(`${Math.floor(index / 12)}-${String((index % 12) + 1).padStart(2, "0")}`);
  }
  return months;
}

/** A continuous monthly timeline; months without sales stay null. */
export function monthlyTimelineData(points: SeriesPoint[], measure: Measure): ChartSeries<string> {
  const labels = monthRange(points);
  const values = new Map(points.map((point) => [point.periodo, point[measure]]));
  return { labels, series: [{ key: "total", values: labels.map((label) => values.get(label) ?? null) }] };
}

/** One line per category over the shared monthly timeline. */
export function categoryLinesData(points: SeriesPoint[], measure: Measure): ChartSeries<string> {
  const labels = monthRange(points);
  const byCategory = new Map<string, Map<string, number>>();
  for (const point of points) {
    const name = point.categoria ?? "Sin categoría";
    const values = byCategory.get(name) ?? new Map<string, number>();
    values.set(point.periodo, point[measure]);
    byCategory.set(name, values);
  }
  return {
    labels,
    series: [...byCategory.entries()]
      .sort(([a], [b]) => a.localeCompare(b, "es"))
      .map(([key, values]) => ({ key, values: labels.map((label) => values.get(label) ?? null) })),
  };
}

/** Twelve monthly totals of one year. */
export function yearMonthsData(points: SeriesPoint[], year: number, measure: Measure): (number | null)[] {
  const values = Array<number | null>(12).fill(null);
  for (const point of points) {
    if (point.anio === year) values[point.mes - 1] = point[measure];
  }
  return values;
}

export function daysInMonth(year: number, month: number): number {
  return new Date(year, month, 0).getDate();
}

/** Every day of one month; days without sales stay null. */
export function monthDaysData(points: SeriesPoint[], year: number, month: number, measure: Measure): ChartSeries<string> {
  const total = daysInMonth(year, month);
  const values = Array<number | null>(total).fill(null);
  for (const point of points) {
    if (point.anio === year && point.mes === month && point.dia !== null) values[point.dia - 1] = point[measure];
  }
  return {
    labels: Array.from({ length: total }, (_, index) => String(index + 1)),
    series: [{ key: "dia", values }],
  };
}

export function observedYears(points: SeriesPoint[]): number[] {
  return [...new Set(points.map((point) => point.anio))].sort((a, b) => a - b);
}

/** The last month with sales, which the month view opens on. */
export function latestMonth(points: SeriesPoint[]): { year: number; month: number } | null {
  if (!points.length) return null;
  const latest = points.reduce((best, point) =>
    point.anio * 12 + point.mes > best.anio * 12 + best.mes ? point : best,
  );
  return { year: latest.anio, month: latest.mes };
}

/** First and last day of a month, clipped to the active date range. */
export function monthBounds(
  year: number,
  month: number,
  range: { fecha_desde?: string; fecha_hasta?: string },
): { fecha_desde: string; fecha_hasta: string } {
  const prefix = `${year}-${String(month).padStart(2, "0")}`;
  const first = `${prefix}-01`;
  const last = `${prefix}-${String(daysInMonth(year, month)).padStart(2, "0")}`;
  return {
    fecha_desde: range.fecha_desde && range.fecha_desde > first ? range.fecha_desde : first,
    fecha_hasta: range.fecha_hasta && range.fecha_hasta < last ? range.fecha_hasta : last,
  };
}

/** "2025-03" -> "Mar 2025", for axis labels. */
export function periodLabel(period: string): string {
  const [year, month] = period.split("-");
  return `${MONTH_LABELS[Number(month) - 1]} ${year}`;
}
