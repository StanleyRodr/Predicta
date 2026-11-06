import { Line } from "react-chartjs-2";
import { CategoryScale, Chart as ChartJS, Filler, Legend, LineElement, LinearScale, PointElement, Tooltip } from "chart.js";
import type { TemporalMetric } from "../../types/analytics";
import { formatAxisCurrency, formatCurrency } from "../../lib/formatters";
import { EmptyState } from "../ui";

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Legend, Filler);

interface TemporalLineChartProps {
  data: TemporalMetric[];
}

export function temporalChartData(data: TemporalMetric[]) {
  return {
    labels: data.map((item) => item.fecha),
    values: data.map((item) => item.ingresos),
  };
}

export function TemporalLineChart({ data }: TemporalLineChartProps) {
  if (!data.length) return <EmptyState description="No hay movimientos en este rango." title="Sin evolucion temporal" />;

  return (
    <div aria-label="Evolucion diaria de ingresos" className="h-96">
      <Line
        data={{
          labels: temporalChartData(data).labels,
          datasets: [
            {
              label: "Ingresos diarios",
              data: temporalChartData(data).values,
              borderColor: "#55d6be",
              backgroundColor: "rgb(85 214 190 / 0.12)",
              pointBackgroundColor: "#f0b429",
              fill: true,
              tension: 0.25,
            },
          ],
        }}
        options={{
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { labels: { color: "#e6edf3" } },
            tooltip: { callbacks: { label: (context) => ` ${formatCurrency(Number(context.raw))}` } },
          },
          scales: {
            x: { ticks: { color: "#8b949e" }, grid: { color: "#30363d" } },
            y: { ticks: { color: "#8b949e", callback: (value) => formatAxisCurrency(Number(value)) }, grid: { color: "#30363d" } },
          },
        }}
      />
    </div>
  );
}
