import {
  BarElement,
  CategoryScale,
  Chart as ChartJS,
  Legend,
  LinearScale,
  LineElement,
  PointElement,
  Tooltip,
  type ChartOptions,
} from "chart.js";
import { CHART_GRID, CHART_MUTED, CHART_SURFACE, CHART_TEXT } from "../../lib/chartColors";
import { formatAxisCurrency, formatCurrency, formatNumber } from "../../lib/formatters";
import type { Measure } from "../../types/analytics";

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, BarElement, Tooltip, Legend);

export const MEASURE_LABELS: Record<Measure, string> = {
  ingresos: "Monto",
  cantidad: "Cantidad",
};

/** Full value for tooltips: money with cents, or units. */
export function formatMeasure(measure: Measure, value: number): string {
  return measure === "ingresos" ? formatCurrency(value) : `${formatNumber(value)} unidades`;
}

/** Short value for axis ticks. */
export function formatMeasureAxis(measure: Measure, value: number): string {
  return measure === "ingresos" ? formatAxisCurrency(value) : formatNumber(value);
}

function tooltipLabel(measure: Measure) {
  return (context: { raw: unknown; dataset: { label?: string } }) => {
    const label = context.dataset.label ?? "";
    if (context.raw === null || context.raw === undefined) return ` ${label}: sin ventas`;
    return ` ${label}: ${formatMeasure(measure, Number(context.raw))}`;
  };
}

function sharedOptions(measure: Measure, legend: boolean) {
  return {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: legend,
        labels: { color: CHART_TEXT, usePointStyle: true, boxWidth: 8, boxHeight: 8 },
      },
      tooltip: { callbacks: { label: tooltipLabel(measure) } },
    },
    scales: {
      x: { ticks: { color: CHART_MUTED }, grid: { color: CHART_GRID } },
      y: {
        beginAtZero: true,
        ticks: { color: CHART_MUTED, callback: (value: number | string) => formatMeasureAxis(measure, Number(value)) },
        grid: { color: CHART_GRID },
      },
    },
  };
}

/** Line charts: one tooltip lists every series at the hovered period. Money and units never share an axis. */
export function lineChartOptions(measure: Measure, { legend = true }: { legend?: boolean } = {}): ChartOptions<"line"> {
  return { ...sharedOptions(measure, legend), interaction: { mode: "index", intersect: false } };
}

/** Bar charts: the tooltip and clicks follow the bar under the pointer. */
export function barChartOptions(measure: Measure, { legend = true }: { legend?: boolean } = {}): ChartOptions<"bar"> {
  return { ...sharedOptions(measure, legend), interaction: { mode: "nearest", intersect: true } };
}

/** Marker shapes, so series that share a chart differ by shape as well as color. */
export const SERIES_POINT_STYLES = ["circle", "rect", "triangle", "rectRot", "star", "crossRot", "rectRounded", "cross"] as const;

export type SeriesPointStyle = (typeof SERIES_POINT_STYLES)[number];

/** Line style shared by every series: 2px line, ringed markers, gaps for missing periods. */
export function lineDataset(
  label: string,
  values: (number | null)[],
  color: string,
  hidden = false,
  pointStyle: SeriesPointStyle = "circle",
) {
  return {
    label,
    data: values,
    hidden,
    pointStyle,
    borderColor: color,
    backgroundColor: color,
    borderWidth: 2,
    pointRadius: 4,
    pointHoverRadius: 6,
    pointBorderColor: CHART_SURFACE,
    pointBorderWidth: 2,
    spanGaps: false,
    tension: 0.2,
  };
}

/** Shape of the series at `index` in a stable order, cycling like the colors. */
export function seriesPointStyle(index: number): SeriesPointStyle {
  const size = SERIES_POINT_STYLES.length;
  return SERIES_POINT_STYLES[((index % size) + size) % size];
}
