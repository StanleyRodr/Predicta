import { render } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { CategoryBarChart } from "./CategoryBarChart";
import { TemporalLineChart } from "./TemporalLineChart";

interface CapturedOptions {
  plugins: { tooltip: { callbacks: { label: (context: { raw: number }) => string } } };
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

function expectChartFormats() {
  const options = captured.options as CapturedOptions;
  expect(options.scales.y.ticks.callback(12000)).toBe("$12,000");
  expect(options.plugins.tooltip.callbacks.label({ raw: 1234.5 })).toBe(" $1,234.50");
}

describe("chart number formats", () => {
  beforeEach(() => {
    captured.options = undefined;
  });

  it("formats the category chart axis and tooltip", () => {
    render(<CategoryBarChart data={[{ categoria: "Bebidas", ingresos_totales: 1234.5, cantidad_ventas: 2, ticket_promedio: 617.25 }]} />);
    expectChartFormats();
  });

  it("formats the temporal chart axis and tooltip", () => {
    render(<TemporalLineChart data={[{ fecha: "2026-01-15", ingresos: 1234.5, ventas_realizadas: 2 }]} />);
    expectChartFormats();
  });
});
