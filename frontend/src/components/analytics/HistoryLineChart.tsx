import { Line } from "react-chartjs-2";
import { SERIES_COLORS } from "../../lib/chartColors";
import { monthlyTimelineData, periodLabel } from "../../lib/seriesTransforms";
import type { Measure, SeriesPoint } from "../../types/analytics";
import { ChartFrame, chartTableRows, EmptyState } from "../ui";
import { formatMeasure, lineDataset, MEASURE_LABELS, lineChartOptions } from "./seriesChart";

interface HistoryLineChartProps {
  points: SeriesPoint[];
  measure: Measure;
}

/** The whole history month by month, as one continuous line. */
export function HistoryLineChart({ points, measure }: HistoryLineChartProps) {
  if (!points.length) return <EmptyState description="No hay ventas en este rango." title="Sin historial" />;
  const data = monthlyTimelineData(points, measure);
  const labels = data.labels.map(periodLabel);
  const values = data.series[0].values;

  return (
    <ChartFrame
      className="h-80 sm:h-96"
      label={`${MEASURE_LABELS[measure]} mensual de todo el historial`}
      table={{
        rowHeader: "Mes",
        columns: [MEASURE_LABELS[measure]],
        rows: chartTableRows(labels, [values], (value) => formatMeasure(measure, value)),
      }}
    >
      <Line
        data={{ labels, datasets: [lineDataset(MEASURE_LABELS[measure], values, SERIES_COLORS[0])] }}
        options={lineChartOptions(measure, { legend: false })}
      />
    </ChartFrame>
  );
}
