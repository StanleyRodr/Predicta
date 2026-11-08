import { useState } from "react";
import { Line } from "react-chartjs-2";
import { yearColor } from "../../lib/chartColors";
import { yearOverlayData } from "../../lib/seriesTransforms";
import type { Measure, SeriesPoint } from "../../types/analytics";
import { EmptyState } from "../ui";
import { lineDataset, MEASURE_LABELS, lineChartOptions } from "./seriesChart";

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
      <div aria-label={`${label}: ${MEASURE_LABELS[measure]} por mes, un año por línea`} className="h-80 sm:h-96" role="img">
        <Line
          data={{
            labels: data.labels,
            datasets: data.series.map((series) =>
              lineDataset(String(series.key), series.values, yearColor(series.key), shown !== null && series.key !== shown),
            ),
          }}
          options={lineChartOptions(measure)}
        />
      </div>
    </div>
  );
}
