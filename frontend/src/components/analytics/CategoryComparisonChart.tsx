import { Line } from "react-chartjs-2";
import { categoryColor } from "../../lib/chartColors";
import { categoryLinesData, periodLabel } from "../../lib/seriesTransforms";
import type { Measure, SeriesPoint } from "../../types/analytics";
import { ChartFrame, chartTableRows, EmptyState } from "../ui";
import { formatMeasure, lineDataset, MEASURE_LABELS, lineChartOptions, seriesPointStyle } from "./seriesChart";

interface CategoryComparisonChartProps {
  points: SeriesPoint[];
  measure: Measure;
  /** Every category the user has, so each keeps its color under any filter. */
  allCategories: string[];
}

/** One line per category over the months of the range. */
export function CategoryComparisonChart({ points, measure, allCategories }: CategoryComparisonChartProps) {
  if (!points.length) return <EmptyState description="No hay ventas en este rango." title="Sin categorías para comparar" />;
  const data = categoryLinesData(points, measure);
  const labels = data.labels.map(periodLabel);
  // Shape follows the category, like its color.
  const ordered = [...new Set(allCategories)].sort((a, b) => a.localeCompare(b, "es"));

  return (
    <ChartFrame
      className="h-80 sm:h-96"
      label={`${MEASURE_LABELS[measure]} mensual por categoría`}
      table={{
        rowHeader: "Mes",
        columns: data.series.map((series) => series.key),
        rows: chartTableRows(
          labels,
          data.series.map((series) => series.values),
          (value) => formatMeasure(measure, value),
        ),
      }}
    >
      <Line
        data={{
          labels,
          datasets: data.series.map((series) =>
            lineDataset(
              series.key,
              series.values,
              categoryColor(series.key, allCategories),
              false,
              seriesPointStyle(ordered.indexOf(series.key)),
            ),
          ),
        }}
        options={lineChartOptions(measure)}
      />
    </ChartFrame>
  );
}
