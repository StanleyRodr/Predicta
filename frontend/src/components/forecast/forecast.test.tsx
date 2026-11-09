import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import type { MonthlyForecastResponse, ProjectedMonth, SavedBatch, ValidationMetrics } from "../../types/forecast";
import { forecastChartTable } from "./ForecastChart";
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
    producto: null,
    modelo: "tendencia",
    horizonte_aplicado: 2,
    meses_observados: 3,
    advertencias: [],
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

describe("forecastChartTable", () => {
  it("lists history, projection, range, and extrapolation as text", () => {
    const table = forecastChartTable(forecast(), "monto");

    expect(table.columns).toEqual(["Historial", "Proyección", "Intervalo del 95 %", "Nota"]);
    expect(table.rows.map((row) => row.label)).toEqual(["Ene 2025", "Feb 2025", "Abr 2025", "May 2025", "Jun 2025"]);
    expect(table.rows[0].values).toEqual(["$100.00", "—", "—", "—"]);
    expect(table.rows[3].values).toEqual(["—", "$150.00", "$140.00 a $160.00", "—"]);
    expect(table.rows[4].values).toEqual(["—", "$160.00", "$150.00 a $170.00", "Extrapolación sin validar"]);
  });

  it("shows the incomplete month as partial history and uses units for quantity", () => {
    const table = forecastChartTable(forecast({ mes_parcial: { periodo: "2025-05", monto: 70, cantidad: 7 } }), "cantidad");

    expect(table.rows[3].values).toEqual(["7 unidades", "15 unidades", "14 unidades a 16 unidades", "Mes en curso (parcial)"]);
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
      producto: null,
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

  it("explains the range and extrapolation once, above the list, not in every batch table", () => {
    const monthlyBatch = (lote: string): SavedBatch => ({
      lote,
      tipo: "mensual",
      categoria: null,
      producto: null,
      modelo: "tendencia",
      horizonte: 2,
      r2_validacion: null,
      wape_validacion: null,
      fecha_creacion: "2026-11-02T10:00:00Z",
      puntos: ["2026-11-30", "2026-12-31"].map((fecha_proyeccion, index) => ({
        fecha_proyeccion,
        extrapolacion: index === 1,
        monto_proyectado: 100,
        monto_inferior: 90,
        monto_superior: 110,
        cantidad_proyectada: 1,
        cantidad_inferior: 0,
        cantidad_superior: 2,
      })),
    });

    render(<SavedPredictions batches={[monthlyBatch("a"), monthlyBatch("b")]} />);

    expect(screen.getAllByRole("button", { name: "Qué significa intervalo del 95 %" })).toHaveLength(1);
    expect(screen.getAllByRole("button", { name: "Qué significa extrapolación" })).toHaveLength(1);
    for (const table of screen.getAllByRole("table", { hidden: true })) {
      expect(within(table).queryAllByRole("button", { hidden: true, name: /Qué significa/ })).toHaveLength(0);
      expect(within(table).getAllByText("Extrapolación")).toHaveLength(1);
    }
  });
});

describe("forecast cards", () => {
  it("shows separate amount and interval values", () => {
    render(<ForecastMetricCard interval={{ inferior: 80, superior: 120 }} label="Monto predicho" value={100} />);

    expect(screen.getByText("Monto predicho")).toBeInTheDocument();
    expect(screen.getByText(/80/)).toBeInTheDocument();
    expect(screen.getByText(/120/)).toBeInTheDocument();
  });

});

describe("ForecastQuality", () => {
  const good: ValidationMetrics = {
    r2: 0.8,
    mape: 12.5,
    rmse: 1250,
    wape: 11,
    mase: 0.6,
    mejora_vs_referencia: 18,
    referencia: "mismo_mes_anio_anterior",
    origenes: 6,
  };
  const empty: ValidationMetrics = {
    r2: null,
    mape: null,
    rmse: null,
    wape: null,
    mase: null,
    mejora_vs_referencia: null,
    referencia: null,
    origenes: 0,
  };

  // Six evaluated months of $10,000 and 100 units: the scale of the typical margin.
  const history = Array.from({ length: 8 }, (_, index) => ({
    periodo: `2025-${String(index + 1).padStart(2, "0")}`,
    monto: 10_000,
    cantidad: 100,
  }));

  function grades(region: HTMLElement) {
    return within(region)
      .getAllByTestId("grade")
      .map((badge) => badge.textContent);
  }

  it("uses plain titles and the right unit for each measure", () => {
    render(<ForecastQuality amount={good} history={history} quantity={{ ...good, mape: 55, rmse: 3.5 }} />);

    const amount = screen.getByRole("region", { name: "Calidad de monto" });
    const quantity = screen.getByRole("region", { name: "Calidad de cantidad" });
    expect(within(amount).getByText("Error promedio")).toBeInTheDocument();
    expect(within(amount).getByText("MAPE")).toBeInTheDocument();
    expect(within(amount).getByText("Se desvía en promedio un 12.50% del valor real.")).toBeInTheDocument();
    expect(within(amount).getByText("Suele fallar por unos $1,250.00.")).toBeInTheDocument();
    expect(within(quantity).getByText("Suele fallar por unos 3.5 unidades.")).toBeInTheDocument();
    expect(within(amount).getByText(/^Calidad buena según 4 indicadores, medida en los últimos 6 meses evaluados/)).toBeInTheDocument();
    expect(screen.getByText(/Las etiquetas son orientativas/)).toBeInTheDocument();
  });

  it("labels every metric and averages them next to the measure", () => {
    render(<ForecastQuality amount={good} history={history} quantity={{ ...good, mape: 55, rmse: 3.5 }} />);

    const amount = screen.getByRole("region", { name: "Calidad de monto" });
    const quantity = screen.getByRole("region", { name: "Calidad de cantidad" });
    // Error 12.5 %, margin 12.5 % of a month, pattern 0.8, 18 % better than the baseline.
    expect(grades(amount)).toEqual(["Error promedio: Buena", "Margen típico: Buena", "Patrón explicado: Muy buena", "Frente a un cálculo simple: Buena"]);
    expect(within(amount).getByTestId("overall-grade")).toHaveTextContent("Calidad general: Buena");
    // Error 55 % is low, margin 3.5 % of a month is very good: (1 + 4 + 4 + 3) / 4 = 3.
    expect(grades(quantity)[0]).toBe("Error promedio: Baja");
    expect(grades(quantity)[1]).toBe("Margen típico: Muy buena");
    expect(within(quantity).getByTestId("overall-grade")).toHaveTextContent("Buena");
  });

  it("shows Sin dato for missing metrics and leaves them out of the average", () => {
    render(<ForecastQuality amount={{ ...good, r2: null, mejora_vs_referencia: null, referencia: null }} history={history} quantity={empty} />);

    const amount = screen.getByRole("region", { name: "Calidad de monto" });
    expect(grades(amount)).toEqual(["Error promedio: Buena", "Margen típico: Buena", "Patrón explicado: Sin dato", "Frente a un cálculo simple: Sin dato"]);
    expect(within(amount).getByText(/según 2 indicadores/)).toBeInTheDocument();
    const quantity = screen.getByRole("region", { name: "Calidad de cantidad" });
    expect(within(quantity).queryByTestId("overall-grade")).not.toBeInTheDocument();
  });

  it("explains each metric on demand", async () => {
    const user = userEvent.setup();
    render(<ForecastQuality amount={good} history={history} quantity={good} />);

    const [hint] = screen.getAllByRole("button", { name: "Qué significa margen típico" });
    await user.click(hint);

    expect(screen.getByRole("note")).toHaveTextContent(/Penaliza más los errores grandes/);
    expect(screen.getByRole("note")).toHaveTextContent(/frente a las ventas de un mes promedio: muy buena si es menos del 10%/);
  });

  it("folds the technical detail and opens and closes it", async () => {
    const user = userEvent.setup();
    render(<ForecastQuality amount={good} history={history} quantity={empty} />);
    const toggle = screen.getByRole("button", { name: "Detalle técnico" });

    expect(toggle).toHaveAttribute("aria-expanded", "false");
    expect(screen.queryByRole("table")).not.toBeInTheDocument();

    await user.click(toggle);
    const table = screen.getByRole("table", { name: "Métricas técnicas de la validación" });
    for (const acronym of ["R²", "MAPE", "RMSE", "WAPE", "MASE"]) {
      expect(within(table).getByRole("rowheader", { name: acronym })).toBeInTheDocument();
    }
    expect(within(within(table).getByRole("rowheader", { name: "WAPE" }).closest("tr") as HTMLElement).getAllByRole("cell").map((cell) => cell.textContent)).toEqual([
      "11.00%",
      "No disponible",
    ]);

    await user.click(toggle);
    expect(screen.queryByRole("table")).not.toBeInTheDocument();
  });

  it("does not represent null metrics as zero and says why they are missing", () => {
    render(<ForecastQuality amount={empty} history={history} quantity={empty} />);

    expect(screen.getAllByText(/^No disponible\. Tu historial todavía no deja meses/)).toHaveLength(8);
    expect(screen.getAllByText(/^Aún no se puede calificar/)).toHaveLength(2);
    expect(screen.queryByText(/\$0\.00|\b0\.00%/)).not.toBeInTheDocument();
  });
});
