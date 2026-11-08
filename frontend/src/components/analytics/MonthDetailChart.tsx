import { Bar, Line } from "react-chartjs-2";
import type { ChartOptions } from "chart.js";
import { SERIES_COLORS } from "../../lib/chartColors";
import { MONTH_LABELS, MONTH_NAMES, monthDaysData, yearMonthsData } from "../../lib/seriesTransforms";
import type { Measure, SeriesPoint } from "../../types/analytics";
import { ChartFrame, chartTableRows, EmptyState } from "../ui";
import { barChartOptions, formatMeasure, lineChartOptions, lineDataset, MEASURE_LABELS } from "./seriesChart";

const BAR_COLOR = SERIES_COLORS[0];
const BAR_DIMMED = "rgb(57 135 229 / 0.45)";

interface MonthTotalsChartProps {
  points: SeriesPoint[];
  year: number;
  measure: Measure;
  selectedMonth: number;
  onSelectMonth: (month: number) => void;
}

/** Twelve monthly totals of one year; clicking a bar opens its daily detail. */
export function MonthTotalsChart({ points, year, measure, selectedMonth, onSelectMonth }: MonthTotalsChartProps) {
  const values = yearMonthsData(points, year, measure);
  if (values.every((value) => value === null)) {
    return <EmptyState description={`No hay ventas en ${year}.`} title="Sin datos en el año" />;
  }
  const options: ChartOptions<"bar"> = {
    ...barChartOptions(measure, { legend: false }),
    onClick: (_event, elements) => {
      const element = elements[0];
      if (element && values[element.index] !== null) onSelectMonth(element.index + 1);
    },
  };

  return (
    <ChartFrame
      className="h-64 sm:h-72"
      description="Elige un mes en el gráfico o en el selector para ver sus días."
      label={`${MEASURE_LABELS[measure]} por mes de ${year}`}
      table={{
        rowHeader: "Mes",
        columns: [MEASURE_LABELS[measure]],
        rows: chartTableRows(MONTH_NAMES, [values], (value) => formatMeasure(measure, value)),
      }}
    >
      <Bar
        data={{
          labels: MONTH_LABELS,
          datasets: [
            {
              label: String(year),
              data: values,
              backgroundColor: values.map((_, index) => (index + 1 === selectedMonth ? BAR_COLOR : BAR_DIMMED)),
              borderRadius: 4,
              borderSkipped: "bottom",
              maxBarThickness: 48,
            },
          ],
        }}
        options={options}
      />
    </ChartFrame>
  );
}

interface MonthDetailChartProps {
  points: SeriesPoint[];
  year: number;
  month: number;
  measure: Measure;
}

/** Every day of one month; days without sales are gaps. */
export function MonthDetailChart({ points, year, month, measure }: MonthDetailChartProps) {
  const title = `${MONTH_NAMES[month - 1]} ${year}`;
  if (!points.length) return <EmptyState description={`No hay ventas en ${title}.`} title="Sin ventas en el mes" />;
  const data = monthDaysData(points, year, month, measure);

  return (
    <ChartFrame
      className="h-64 sm:h-72"
      label={`${MEASURE_LABELS[measure]} por día de ${title}`}
      table={{
        rowHeader: "Día",
        columns: [MEASURE_LABELS[measure]],
        rows: chartTableRows(data.labels.map(String), [data.series[0].values], (value) => formatMeasure(measure, value)),
      }}
    >
      <Line
        data={{ labels: data.labels, datasets: [lineDataset(title, data.series[0].values, SERIES_COLORS[0])] }}
        options={lineChartOptions(measure, { legend: false })}
      />
    </ChartFrame>
  );
}
