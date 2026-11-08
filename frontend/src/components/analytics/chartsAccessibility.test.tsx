import { render, screen, within } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import type { SeriesPoint } from "../../types/analytics";
import { CategoryBarChart } from "./CategoryBarChart";
import { CategoryComparisonChart } from "./CategoryComparisonChart";
import { HistoryLineChart } from "./HistoryLineChart";
import { MonthDetailChart, MonthTotalsChart } from "./MonthDetailChart";
import { lineDataset, seriesPointStyle } from "./seriesChart";
import { YearOverlayChart } from "./YearOverlayChart";

interface CapturedDataset {
  label: string;
  pointStyle?: string;
}

const charts = vi.hoisted(() => ({ last: [] as { datasets: CapturedDataset[] }[] }));

vi.mock("react-chartjs-2", () => {
  const Chart = ({ data }: { data: { datasets: CapturedDataset[] } }) => {
    charts.last.push(data);
    return <canvas />;
  };
  return { Bar: Chart, Line: Chart };
});

function point(anio: number, mes: number, extra: Partial<SeriesPoint> = {}): SeriesPoint {
  return {
    periodo: `${anio}-${String(mes).padStart(2, "0")}`,
    anio,
    mes,
    dia: null,
    categoria: null,
    ingresos: 1000 * mes,
    cantidad: mes,
    ventas_realizadas: 1,
    ...extra,
  };
}

/** The values of the row whose header is `label`. */
function rowValues(table: HTMLElement, label: string): string[] {
  const row = within(table).getByRole("rowheader", { name: label }).closest("tr") as HTMLElement;
  return within(row)
    .getAllByRole("cell")
    .map((cell) => cell.textContent ?? "");
}

describe("accessible charts", () => {
  it("names the category bar chart and lists its values", () => {
    render(
      <CategoryBarChart
        data={[
          { categoria: "Bebidas", ingresos_totales: 1234.5, cantidad_ventas: 2, ticket_promedio: 617.25 },
          { categoria: "Lácteos", ingresos_totales: 80, cantidad_ventas: 1, ticket_promedio: 80 },
        ]}
      />,
    );

    expect(screen.getByRole("img", { name: "Ingresos por categoría" })).toBeInTheDocument();
    const table = screen.getByRole("table", { name: "Datos de Ingresos por categoría" });
    expect(rowValues(table, "Bebidas")).toEqual(["$1,234.50"]);
    expect(rowValues(table, "Lácteos")).toEqual(["$80.00"]);
  });

  it("lists every year of the overlay, with months without sales as text", () => {
    render(<YearOverlayChart label="Todas las categorías" measure="ingresos" points={[point(2024, 1), point(2025, 1), point(2025, 3)]} />);

    const table = screen.getByRole("table", { name: /un año por línea/ });
    expect(within(table).getByRole("columnheader", { name: "2024" })).toBeInTheDocument();
    expect(rowValues(table, "Enero")).toEqual(["$1,000.00", "$1,000.00"]);
    expect(rowValues(table, "Marzo")).toEqual(["Sin ventas", "$3,000.00"]);
  });

  it("lists categories per month and gives each line its own shape", () => {
    charts.last = [];
    render(
      <CategoryComparisonChart
        allCategories={["Lácteos", "Bebidas"]}
        measure="cantidad"
        points={[point(2025, 1, { categoria: "Bebidas", cantidad: 3 }), point(2025, 1, { categoria: "Lácteos", cantidad: 5 })]}
      />,
    );

    const table = screen.getByRole("table", { name: "Datos de Cantidad mensual por categoría" });
    expect(rowValues(table, "Ene 2025")).toEqual(["3 unidades", "5 unidades"]);
    const styles = charts.last.at(-1)?.datasets.map((dataset) => dataset.pointStyle);
    expect(new Set(styles).size).toBe(2);
  });

  it("describes the history, the monthly totals, and the daily detail", () => {
    render(
      <>
        <HistoryLineChart measure="ingresos" points={[point(2025, 1), point(2025, 3)]} />
        <MonthTotalsChart measure="ingresos" onSelectMonth={() => undefined} points={[point(2025, 2)]} selectedMonth={2} year={2025} />
        <MonthDetailChart measure="ingresos" month={3} points={[point(2025, 3, { dia: 4, periodo: "2025-03-04", ingresos: 50 })]} year={2025} />
      </>,
    );

    const history = screen.getByRole("table", { name: "Datos de Monto mensual de todo el historial" });
    expect(rowValues(history, "Feb 2025")).toEqual(["Sin ventas"]);
    const totals = screen.getByRole("img", { name: "Monto por mes de 2025" });
    expect(totals).toHaveAccessibleDescription(/Elige un mes/);
    expect(rowValues(screen.getByRole("table", { name: "Datos de Monto por mes de 2025" }), "Febrero")).toEqual(["$2,000.00"]);
    expect(rowValues(screen.getByRole("table", { name: "Datos de Monto por día de Marzo 2025" }), "4")).toEqual(["$50.00"]);
  });

  it("never leaves a chart label on a div without a role", () => {
    const { container } = render(<HistoryLineChart measure="cantidad" points={[point(2025, 1)]} />);

    for (const element of container.querySelectorAll("div[aria-label]")) {
      expect(element).toHaveAttribute("role", "img");
    }
  });

  it("cycles marker shapes like colors", () => {
    expect(lineDataset("A", [1], "#000").pointStyle).toBe("circle");
    expect(seriesPointStyle(1)).toBe("rect");
    expect(seriesPointStyle(8)).toBe(seriesPointStyle(0));
    expect(seriesPointStyle(-1)).toBe(seriesPointStyle(7));
  });
});
