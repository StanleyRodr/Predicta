import { render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import type { MonthlyForecastResponse, ProjectedMonth, SavedBatch } from "../../types/forecast";
import { forecastChartData } from "./forecastChartData";
import { ForecastMetricCard } from "./ForecastMetricCard";
import { ForecastQuality } from "./ForecastQuality";
import { ForecastTable } from "./ForecastTable";
import { MonthDetail } from "./MonthDetail";
import { SavedPredictions } from "./SavedPredictions";

function projected(periodo: string, monto: number, extrapolacion = false): ProjectedMonth {
  return {
    periodo,
    extrapolacion,
    monto: { prediccion: monto, inferior: monto - 10, superior: monto + 10 },
    cantidad: { prediccion: monto / 10, inferior: monto / 10 - 1, superior: monto / 10 + 1 },
  };
}

function forecast(overrides: Partial<MonthlyForecastResponse> = {}): MonthlyForecastResponse {
  return {
    usuario: "ana",
    categoria: null,
    modelo: "tendencia",
    horizonte_aplicado: 2,
    meses_observados: 3,
    advertencia: null,
    historial: [
      { periodo: "2025-01", monto: 100, cantidad: 10 },
      { periodo: "2025-02", monto: 120, cantidad: 12 },
      { periodo: "2025-04", monto: 140, cantidad: 14 },
    ],
    mes_parcial: null,
    proyeccion: [projected("2025-05", 150), projected("2025-06", 160, true)],
    metricas: {
      monto: { r2: null, mape: 5, rmse: 3, wape: 4, mase: 0.5, mejora_vs_referencia: 10, referencia: "ultimo_valor", origenes: 3 },
      cantidad: { r2: null, mape: 5, rmse: 3, wape: 4, mase: 0.5, mejora_vs_referencia: 10, referencia: "ultimo_valor", origenes: 3 },
    },
    ...overrides,
  };
}

describe("forecastChartData", () => {
  it("uses only the periods and values the backend sent", () => {
    const data = forecastChartData(forecast(), "monto");

    expect(data.periodos).toEqual(["2025-01", "2025-02", "2025-04", "2025-05", "2025-06"]);
    expect(data.historial).toEqual([100, 120, 140, null, null]);
    // The dashed line starts at the last real month, then follows the projection.
    expect(data.proyeccion).toEqual([null, null, 140, 150, 160]);
    expect(data.inferior).toEqual([null, null, null, 140, 150]);
    expect(data.superior).toEqual([null, null, null, 160, 170]);
    expect(data.extrapolacion).toEqual([false, false, false, false, true]);
    expect(data.indiceProyeccion).toEqual([3, 4]);
  });

  it("does not invent the missing March", () => {
    const data = forecastChartData(forecast(), "monto");

    expect(data.periodos).not.toContain("2025-03");
  });

  it("places the incomplete month on the first projected period", () => {
    const data = forecastChartData(forecast({ mes_parcial: { periodo: "2025-05", monto: 70, cantidad: 7 } }), "monto");

    expect(data.parcial).toEqual([null, null, null, 70, null]);
    expect(data.proyeccion[3]).toBe(150);
  });

  it("switches every series to units", () => {
    const data = forecastChartData(forecast(), "cantidad");

    expect(data.historial.slice(0, 3)).toEqual([10, 12, 14]);
    expect(data.proyeccion[3]).toBe(15);
  });

  it("keeps only the latest months of a long history", () => {
    const data = forecastChartData(forecast(), "monto", 2);

    expect(data.periodos).toEqual(["2025-02", "2025-04", "2025-05", "2025-06"]);
  });
});

describe("ForecastTable", () => {
  it("shows normal values, zero, and missing values differently", () => {
    render(
      <ForecastTable
        caption="Meses"
        measure="monto"
        rows={[
          { periodo: "2025-05", monto: 1234.5, cantidad: 12, inferior: 1000, superior: 1500, extrapolacion: false },
          { periodo: "2025-06", monto: 0, cantidad: 0, inferior: 0, superior: 50, extrapolacion: true },
          { periodo: "2025-07", monto: null, cantidad: 3, inferior: null, superior: null, extrapolacion: null },
        ]}
      />,
    );

    const [normal, zero, missing] = screen.getAllByRole("row").slice(1);
    expect(normal).toHaveTextContent("$1,234.50");
    expect(normal).toHaveTextContent("$1,000.00 – $1,500.00");
    expect(zero).toHaveTextContent("$0.00");
    expect(within(zero).getByText("Extrapolación")).toBeInTheDocument();
    expect(missing).toHaveTextContent("—");
    expect(missing).not.toHaveTextContent("$0.00");
  });

  it("marks the selected month", () => {
    render(
      <ForecastTable
        caption="Meses"
        measure="cantidad"
        onSelect={() => undefined}
        rows={[{ periodo: "2025-05", monto: 1, cantidad: 2, inferior: 1, superior: 3, extrapolacion: false }]}
        selected="2025-05"
      />,
    );

    expect(screen.getAllByRole("row")[1]).toHaveAttribute("aria-selected", "true");
    expect(screen.getByRole("columnheader", { name: /Rango 95 % \(cantidad\)/ })).toBeInTheDocument();
  });
});

describe("MonthDetail", () => {
  it("notes when the month is an extrapolation", () => {
    render(<MonthDetail month={projected("2025-11", 150, true)} />);

    expect(screen.getByRole("region", { name: "Detalle de Nov 2025" })).toHaveTextContent("$150.00");
    expect(screen.getByText(/es una extrapolación/)).toBeInTheDocument();
  });

  it("adds no note inside the validated months", () => {
    render(<MonthDetail month={projected("2025-05", 150)} />);

    expect(screen.queryByText(/es una extrapolación/)).not.toBeInTheDocument();
  });
});

describe("SavedPredictions", () => {
  it("invites the user to save when the list is empty", () => {
    render(<SavedPredictions batches={[]} />);

    expect(screen.getByText("Aún no guardas proyecciones")).toBeInTheDocument();
  });

  it("names old daily rows and shows each batch total", () => {
    const daily: SavedBatch = {
      lote: "legado-1",
      tipo: "diaria",
      categoria: null,
      modelo: null,
      horizonte: null,
      r2_validacion: 0.22,
      wape_validacion: null,
      fecha_creacion: "2026-11-02T10:00:00Z",
      puntos: [
        {
          fecha_proyeccion: "2026-11-01",
          extrapolacion: null,
          monto_proyectado: 8036.56,
          monto_inferior: null,
          monto_superior: null,
          cantidad_proyectada: 216.33,
          cantidad_inferior: null,
          cantidad_superior: null,
        },
      ],
    };

    render(<SavedPredictions batches={[daily]} />);

    expect(screen.getByText("Proyección diaria (anterior)")).toBeInTheDocument();
    expect(screen.getByText(/total \$8,036\.56/)).toBeInTheDocument();
    expect(screen.getByText(/^0?1\/11\/2026$/)).toBeInTheDocument();
  });
});

describe("forecast cards", () => {
  it("shows separate amount and interval values", () => {
    render(<ForecastMetricCard interval={{ inferior: 80, superior: 120 }} label="Monto predicho" value={100} />);

    expect(screen.getByText("Monto predicho")).toBeInTheDocument();
    expect(screen.getByText(/80/)).toBeInTheDocument();
    expect(screen.getByText(/120/)).toBeInTheDocument();
  });

  it("does not represent null metrics as zero", () => {
    render(
      <ForecastQuality
        amount={{ r2: null, mape: null, rmse: null }}
        quantity={{ r2: 0.8, mape: 2, rmse: 1 }}
      />,
    );

    expect(screen.getAllByText("No disponible")).toHaveLength(3);
    expect(screen.getByText("0.80")).toBeInTheDocument();
  });
});
