import { render } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type { SeriesPoint } from "../../types/analytics";
import { CategoryBarChart } from "./CategoryBarChart";
import { HistoryLineChart } from "./HistoryLineChart";

interface TooltipContext {
  raw: number | null;
  dataset: { label: string };
}

interface CapturedOptions {
  plugins: { tooltip: { callbacks: { label: (context: TooltipContext) => string } } };
  scales: { y: { ticks: { callback: (value: number) => string } } };
}

const captured = vi.hoisted(() => ({ options: undefined as unknown }));

vi.mock("react-chartjs-2", () => {
  const Chart = ({ options }: { options: unknown }) => {
    captured.options = options;
    return null;
  };
  return { Bar: Chart, Line: Chart };
});

const point: SeriesPoint = {
  periodo: "2026-01",
  anio: 2026,
  mes: 1,
  dia: null,
  categoria: null,
  ingresos: 1234.5,
  cantidad: 1500,
  ventas_realizadas: 3,
};

function options() {
  return captured.options as CapturedOptions;
}

describe("chart number formats", () => {
  beforeEach(() => {
    captured.options = undefined;
  });

  it("formats the category chart axis and tooltip", () => {
    render(<CategoryBarChart data={[{ categoria: "Bebidas", ingresos_totales: 1234.5, cantidad_ventas: 2, ticket_promedio: 617.25 }]} />);
    expect(options().scales.y.ticks.callback(12000)).toBe("$12,000");
    expect(options().plugins.tooltip.callbacks.label({ raw: 1234.5, dataset: { label: "Ingresos" } })).toBe(" $1,234.50");
  });

  it("uses dollars for the amount measure", () => {
    render(<HistoryLineChart measure="ingresos" points={[point]} />);
    expect(options().scales.y.ticks.callback(12000)).toBe("$12,000");
    expect(options().plugins.tooltip.callbacks.label({ raw: 1234.5, dataset: { label: "Monto" } })).toBe(" Monto: $1,234.50");
  });

  it("uses units, never dollars, for the quantity measure", () => {
    render(<HistoryLineChart measure="cantidad" points={[point]} />);
    expect(options().scales.y.ticks.callback(1500)).toBe("1,500");
    expect(options().plugins.tooltip.callbacks.label({ raw: 1500, dataset: { label: "Cantidad" } })).toBe(
      " Cantidad: 1,500 unidades",
    );
  });

  it("names a gap as a period without sales", () => {
    render(<HistoryLineChart measure="ingresos" points={[point]} />);
    expect(options().plugins.tooltip.callbacks.label({ raw: null, dataset: { label: "2024" } })).toBe(" 2024: sin ventas");
  });
});
