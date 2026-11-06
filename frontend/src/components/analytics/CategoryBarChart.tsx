import { Bar } from "react-chartjs-2";
import { BarElement, CategoryScale, Chart as ChartJS, Legend, LinearScale, Tooltip } from "chart.js";
import type { CategoryMetric } from "../../types/analytics";
import { formatAxisCurrency, formatCurrency } from "../../lib/formatters";
import { EmptyState } from "../ui";

ChartJS.register(CategoryScale, LinearScale, BarElement, Tooltip, Legend);

interface CategoryBarChartProps {
  data: CategoryMetric[];
}

export function categoryChartData(data: CategoryMetric[]) {
  return {
    labels: data.map((item) => item.categoria),
    values: data.map((item) => item.ingresos_totales),
  };
}

export function CategoryBarChart({ data }: CategoryBarChartProps) {
  if (!data.length) return <EmptyState description="No hay categorias en este rango." title="Sin categorias" />;

  return (
    <div aria-label="Ingresos por categoria" className="h-80">
      <Bar
        data={{
          labels: categoryChartData(data).labels,
          datasets: [
            {
              label: "Ingresos",
              data: categoryChartData(data).values,
              backgroundColor: "#f0b429",
              borderColor: "#f0b429",
              borderWidth: 1,
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
