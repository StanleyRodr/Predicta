import { Line } from "react-chartjs-2";
import { SERIES_COLORS } from "../../lib/chartColors";
import { monthlyTimelineData, periodLabel } from "../../lib/seriesTransforms";
import type { Measure, SeriesPoint } from "../../types/analytics";
import { EmptyState } from "../ui";
import { lineDataset, MEASURE_LABELS, lineChartOptions } from "./seriesChart";

interface HistoryLineChartProps {
  points: SeriesPoint[];
  measure: Measure;
}

/** The whole history month by month, as one continuous line. */
export function HistoryLineChart({ points, measure }: HistoryLineChartProps) {
  if (!points.length) return <EmptyState description="No hay ventas en este rango." title="Sin historial" />;
  const data = monthlyTimelineData(points, measure);

  return (
    <div aria-label={`${MEASURE_LABELS[measure]} mensual de todo el historial`} className="h-80 sm:h-96" role="img">
      <Line
        data={{ labels: data.labels.map(periodLabel), datasets: [lineDataset(MEASURE_LABELS[measure], data.series[0].values, SERIES_COLORS[0])] }}
        options={lineChartOptions(measure, { legend: false })}
      />
    </div>
  );
}
