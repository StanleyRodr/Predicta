import { fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { categoryChartData } from "./CategoryBarChart";
import { DateRangeFilter } from "./DateRangeFilter";
import { temporalChartData } from "./TemporalLineChart";

describe("analytics components", () => {
  it("builds chart data from backend values without re-aggregating", () => {
    expect(categoryChartData([{ categoria: "Abarrotes", ingresos_totales: 20, cantidad_ventas: 2, ticket_promedio: 10 }])).toEqual({
      labels: ["Abarrotes"],
      values: [20],
    });
    expect(temporalChartData([{ fecha: "2026-01-01", ingresos: 12, ventas_realizadas: 1 }])).toEqual({
      labels: ["2026-01-01"],
      values: [12],
    });
  });

  it("rejects inverted ranges and clears applied values", async () => {
    const user = userEvent.setup();
    const onApply = vi.fn();
    const onClear = vi.fn();
    render(<DateRangeFilter onApply={onApply} onClear={onClear} value={{}} />);

    fireEvent.change(screen.getByLabelText("Fecha desde"), { target: { value: "2026-02-01" } });
    fireEvent.change(screen.getByLabelText("Fecha hasta"), { target: { value: "2026-01-01" } });
    await user.click(screen.getByRole("button", { name: "Aplicar filtro" }));
    expect(screen.getByRole("alert")).toHaveTextContent("fecha inicial");
    expect(onApply).not.toHaveBeenCalled();

    await user.click(screen.getByRole("button", { name: "Limpiar" }));
    expect(onClear).toHaveBeenCalledOnce();
  });
});
