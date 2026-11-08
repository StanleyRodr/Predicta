import { Line } from "react-chartjs-2";
import { categoryColor } from "../../lib/chartColors";
import { categoryLinesData, periodLabel } from "../../lib/seriesTransforms";
import type { Measure, SeriesPoint } from "../../types/analytics";
import { EmptyState } from "../ui";
import { lineDataset, MEASURE_LABELS, lineChartOptions } from "./seriesChart";

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

  return (
    <div aria-label={`${MEASURE_LABELS[measure]} mensual por categoría`} className="h-80 sm:h-96" role="img">
      <Line
        data={{
          labels: data.labels.map(periodLabel),
          datasets: data.series.map((series) =>
            lineDataset(series.key, series.values, categoryColor(series.key, allCategories)),
          ),
        }}
        options={lineChartOptions(measure)}
      />
    </div>
  );
}
