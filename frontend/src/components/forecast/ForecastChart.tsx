import {
  CategoryScale,
  Chart as ChartJS,
  Filler,
  Legend,
  LinearScale,
  LineElement,
  PointElement,
  Tooltip,
  type ChartOptions,
  type ScriptableLineSegmentContext,
} from "chart.js";
import { Line } from "react-chartjs-2";
import { CHART_GRID, CHART_MUTED, CHART_SURFACE, CHART_TEXT, SERIES_COLORS } from "../../lib/chartColors";
import { formatAxisCurrency, formatCurrency, formatNumber } from "../../lib/formatters";
import { periodLabel } from "../../lib/seriesTransforms";
import type { MonthlyForecastResponse } from "../../types/forecast";
import { ChartFrame, type ChartTable } from "../ui";
import { FORECAST_MEASURES, forecastChartData, type ForecastMeasure } from "./forecastChartData";

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Filler, Tooltip, Legend);

const HISTORY_COLOR = SERIES_COLORS[0];
const PROJECTION_COLOR = SERIES_COLORS[1];
const BAND_COLOR = "rgb(217 89 38 / 0.18)";

export const BAND_LABEL = "Intervalo del 95 %";

export function formatForecastValue(measure: ForecastMeasure, value: number): string {
  return measure === "monto" ? formatCurrency(value) : `${formatNumber(value)} unidades`;
}

interface ForecastChartProps {
  forecast: MonthlyForecastResponse;
  measure: ForecastMeasure;
  /** YYYY-MM of the highlighted projected month. */
  selected: string | null;
  onSelect: (periodo: string) => void;
}

/** Text equivalent of the chart: one row per period, with the range and the extrapolation mark. */
export function forecastChartTable(forecast: MonthlyForecastResponse, measure: ForecastMeasure): ChartTable {
  const data = forecastChartData(forecast, measure);
  const projected = new Set(data.indiceProyeccion);
  const show = (value: number | null) => (value === null ? "—" : formatForecastValue(measure, value));
  return {
    rowHeader: "Mes",
    columns: ["Historial", "Proyección", BAND_LABEL, "Nota"],
    rows: data.periodos.map((periodo, index) => {
      const partial = data.parcial[index];
      // History holds only months the backend sent, so a null here is a future month.
      const history = data.historial[index] ?? partial;
      const notes = [
        partial !== null ? "Mes en curso (parcial)" : "",
        data.extrapolacion[index] ? "Extrapolación sin validar" : "",
      ].filter(Boolean);
      return {
        label: periodLabel(periodo),
        values: [
          show(history),
          projected.has(index) ? show(data.proyeccion[index]) : "—",
          projected.has(index) && data.inferior[index] !== null && data.superior[index] !== null
            ? `${show(data.inferior[index])} a ${show(data.superior[index])}`
            : "—",
          notes.join("; ") || "—",
        ],
      };
    }),
  };
}

/** Solid history, dashed projection, and the 95 % band between its bounds. */
export function ForecastChart({ forecast, measure, selected, onSelect }: ForecastChartProps) {
  const data = forecastChartData(forecast, measure);
  const selectedIndex = selected ? data.periodos.indexOf(selected) : -1;
  const extrapolated = (index: number) => data.extrapolacion[index] ?? false;
  const projectionIndex = new Set(data.indiceProyeccion);

  const options: ChartOptions<"line"> = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: { mode: "index", intersect: false },
    onClick: (_event, elements) => {
      const index = elements.find((element) => projectionIndex.has(element.index))?.index;
      if (index !== undefined) onSelect(data.periodos[index]);
    },
    plugins: {
      legend: {
        labels: {
          color: CHART_TEXT,
          usePointStyle: true,
          boxWidth: 8,
          boxHeight: 8,
          filter: (item) => item.text !== "",
        },
      },
      tooltip: {
        filter: (item) => item.raw !== null && item.dataset.label !== "",
        callbacks: {
          label: (context) => ` ${context.dataset.label}: ${formatForecastValue(measure, Number(context.raw))}`,
          afterBody: (items) => {
            const index = items[0]?.dataIndex;
            return index !== undefined && extrapolated(index) ? ["Extrapolación sin validar"] : [];
          },
        },
      },
    },
    scales: {
      x: { ticks: { color: CHART_MUTED, maxRotation: 45 }, grid: { color: CHART_GRID } },
      y: {
        beginAtZero: true,
        ticks: {
          color: CHART_MUTED,
          callback: (value) => (measure === "monto" ? formatAxisCurrency(Number(value)) : formatNumber(Number(value))),
        },
        grid: { color: CHART_GRID },
      },
    },
  };

  return (
    <ChartFrame
      className="h-80 sm:h-96"
      description="Historial en línea continua, proyección en línea punteada y la zona sombreada del intervalo del 95 %. Los meses en extrapolación usan rombos huecos y un trazo más fino."
      label={`${FORECAST_MEASURES[measure]}: historial y proyección de ${forecast.horizonte_aplicado} meses con intervalo del 95 %`}
      table={forecastChartTable(forecast, measure)}
    >
      <Line
        data={{
          labels: data.periodos.map(periodLabel),
          datasets: [
            {
              label: BAND_LABEL,
              data: data.superior,
              borderWidth: 0,
              pointRadius: 0,
              backgroundColor: BAND_COLOR,
              fill: "+1",
              spanGaps: false,
            },
            {
              label: "",
              data: data.inferior,
              borderWidth: 0,
              pointRadius: 0,
              backgroundColor: BAND_COLOR,
              fill: false,
              spanGaps: false,
            },
            {
              label: "Historial",
              data: data.historial,
              borderColor: HISTORY_COLOR,
              backgroundColor: HISTORY_COLOR,
              borderWidth: 2,
              pointRadius: 3,
              pointBorderColor: CHART_SURFACE,
              pointBorderWidth: 2,
              spanGaps: false,
              tension: 0.2,
            },
            {
              label: "Proyección",
              data: data.proyeccion,
              borderColor: PROJECTION_COLOR,
              backgroundColor: data.periodos.map((_, index) => (extrapolated(index) ? CHART_SURFACE : PROJECTION_COLOR)),
              borderWidth: 2,
              borderDash: [6, 4],
              // Extrapolated months: finer dashes, hollow diamonds.
              segment: {
                borderDash: (context: ScriptableLineSegmentContext) => (extrapolated(context.p1DataIndex) ? [2, 4] : undefined),
              },
              pointStyle: data.periodos.map((_, index) => (extrapolated(index) ? "rectRot" : "circle")),
              pointRadius: data.periodos.map((_, index) => (index === selectedIndex ? 7 : projectionIndex.has(index) ? 4 : 0)),
              pointBorderColor: PROJECTION_COLOR,
              pointBorderWidth: 2,
              spanGaps: false,
              tension: 0.2,
            },
            ...(forecast.mes_parcial
              ? [
                  {
                    label: "Mes en curso (parcial)",
                    data: data.parcial,
                    showLine: false,
                    borderColor: HISTORY_COLOR,
                    backgroundColor: CHART_SURFACE,
                    pointRadius: 5,
                    pointBorderWidth: 2,
                  },
                ]
              : []),
          ],
        }}
        options={options}
      />
    </ChartFrame>
  );
}
