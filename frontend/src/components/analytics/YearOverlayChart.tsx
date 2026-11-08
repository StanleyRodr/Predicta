import { useState } from "react";
import { Line } from "react-chartjs-2";
import { yearColor } from "../../lib/chartColors";
import { MONTH_NAMES, yearOverlayData } from "../../lib/seriesTransforms";
import type { Measure, SeriesPoint } from "../../types/analytics";
import { ChartFrame, chartTableRows, EmptyState } from "../ui";
import { formatMeasure, lineChartOptions, lineDataset, MEASURE_LABELS, seriesPointStyle } from "./seriesChart";

interface YearOverlayChartProps {
  points: SeriesPoint[];
  measure: Measure;
  label: string;
}

/** One line per year on a January-to-December axis, so seasons line up. */
export function YearOverlayChart({ points, measure, label }: YearOverlayChartProps) {
  const [isolated, setIsolated] = useState<number | null>(null);
  const data = yearOverlayData(points, measure);
  const years = data.series.map((series) => series.key);
  const shown = isolated !== null && years.includes(isolated) ? isolated : null;
  const visible = data.series.filter((series) => shown === null || series.key === shown);

  if (!points.length) return <EmptyState description="No hay ventas en este rango." title="Sin datos para comparar" />;

  return (
    <div className="grid gap-3">
      <label className="flex w-fit items-center gap-2 text-sm text-terminal-muted">
        Año
        <select
          className="rounded-md border border-terminal-border bg-terminal-bg px-2 py-1 text-terminal-text"
          onChange={(event) => setIsolated(event.target.value ? Number(event.target.value) : null)}
          value={shown ?? ""}
        >
          <option value="">Todos los años</option>
          {years.map((year) => (
            <option key={year} value={year}>
              {year}
            </option>
          ))}
        </select>
      </label>
      <ChartFrame
        className="h-80 sm:h-96"
        label={`${label}: ${MEASURE_LABELS[measure]} por mes, un año por línea`}
        table={{
          rowHeader: "Mes",
          columns: visible.map((series) => String(series.key)),
          rows: chartTableRows(
            MONTH_NAMES,
            visible.map((series) => series.values),
            (value) => formatMeasure(measure, value),
          ),
        }}
      >
        <Line
          data={{
            labels: data.labels,
            datasets: data.series.map((series) =>
              lineDataset(
                String(series.key),
                series.values,
                yearColor(series.key),
                shown !== null && series.key !== shown,
                seriesPointStyle(series.key),
              ),
            ),
          }}
          options={lineChartOptions(measure)}
        />
      </ChartFrame>
    </div>
  );
}
