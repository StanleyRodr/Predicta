import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { AxiosError, AxiosHeaders } from "axios";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { getCategoryStats, getProducts } from "../api/analytics";
import { getForecast, getMonthlyForecast, listSavedPredictions, savePrediction } from "../api/forecast";
import { useAuthStore } from "../stores/authStore";
import type { User } from "../types/api";
import type { ForecastResponse, MonthlyForecastResponse, ProjectedMonth, SavedBatch } from "../types/forecast";
import { PredictionsPage } from "./PredictionsPage";

vi.mock("../api/forecast", () => ({
  getForecast: vi.fn(),
  getMonthlyForecast: vi.fn(),
  listSavedPredictions: vi.fn(),
  savePrediction: vi.fn(),
}));
vi.mock("../api/analytics", () => ({ getCategoryStats: vi.fn(), getProducts: vi.fn() }));

interface CapturedDataset {
  label: string;
  data: (number | null)[];
  borderDash?: number[];
}

const charts = vi.hoisted(() => ({ last: [] as { datasets: CapturedDataset[] }[] }));

vi.mock("react-chartjs-2", () => ({
  Line: ({ data }: { data: { datasets: CapturedDataset[] } }) => {
    charts.last.push(data);
    return null;
  },
}));

function month(periodo: string, monto: number, extrapolacion = false): ProjectedMonth {
  return {
    periodo,
    extrapolacion,
    monto: { prediccion: monto, inferior: monto - 100, superior: monto + 100 },
    cantidad: { prediccion: monto / 100, inferior: monto / 100 - 1, superior: monto / 100 + 1 },
  };
}

const metrics = { r2: 0.4, mape: 8, mae: 70, rmse: 90, wape: 7, mase: 0.6, mejora_vs_referencia: 12, referencia: "ultimo_valor" as const, origenes: 6 };

function monthly(overrides: Partial<MonthlyForecastResponse> = {}): MonthlyForecastResponse {
  return {
    usuario: "ana",
    categoria: null,
    producto: null,
    modelo: "tendencia",
    horizonte_aplicado: 7,
    meses_observados: 24,
    advertencias: [],
    advertencia: null,
    historial: [
      { periodo: "2026-09", monto: 9000, cantidad: 90 },
      { periodo: "2026-10", monto: 9500, cantidad: 95 },
    ],
    mes_parcial: null,
    proyeccion: [
      month("2026-11", 10000),
      month("2026-12", 12000),
      month("2027-01", 8000),
      month("2027-02", 8100),
      month("2027-03", 9000),
      month("2027-04", 9500),
      month("2027-05", 9900, true),
    ],
    metricas: { monto: metrics, cantidad: metrics },
    ...overrides,
  };
}

const daily: ForecastResponse = {
  usuario: "ana",
  proxima_fecha: "2026-11-01",
  monto_predicho: 321.5,
  cantidad_predicha: 4,
  monto_original_crudo: 321.5,
  intervalos_prediccion: { monto: { inferior: 300, superior: 340 }, cantidad: { inferior: 3, superior: 5 } },
  metricas: { monto: { r2: null, mape: 5, mae: 1.5, rmse: 2 }, cantidad: { r2: null, mape: 5, mae: 1.5, rmse: 2 } },
  mensaje: "Predicción ajustada.",
};

const batch: SavedBatch = {
  lote: "abc",
  tipo: "mensual",
  categoria: "Lácteos",
  producto: null,
  modelo: "tendencia",
  horizonte: 7,
  r2_validacion: 0.4,
  wape_validacion: 7,
  fecha_creacion: "2026-11-08T15:00:00Z",
  puntos: [],
};

function httpError(status: number, detail: string) {
  const config = { headers: new AxiosHeaders() };
  return new AxiosError("Request failed", "ERR_BAD_REQUEST", config, null, {
    status,
    statusText: "",
    headers: {},
    config,
    data: { detail },
  });
}

function renderPage() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <PredictionsPage />
    </QueryClientProvider>,
  );
}

async function calculate(user: ReturnType<typeof userEvent.setup>) {
  await user.click(screen.getByRole("button", { name: "Calcular proyección" }));
}

function lastChart() {
  return charts.last.at(-1)?.datasets ?? [];
}

beforeEach(() => {
  charts.last = [];
  act(() => useAuthStore.setState({ user: { id_usuario: 3 } as User }));
  vi.mocked(getCategoryStats).mockResolvedValue({
    usuario: "ana",
    analisis_por_categoria: [
      { categoria: "Lácteos", ingresos_totales: 300, cantidad_ventas: 3, ticket_promedio: 100 },
      { categoria: "Bebidas", ingresos_totales: 900, cantidad_ventas: 3, ticket_promedio: 300 },
    ],
  });
  vi.mocked(getMonthlyForecast).mockImplementation(async (categoria, producto) =>
    monthly({ categoria: categoria ?? null, producto: producto ?? null }),
  );
  vi.mocked(getProducts).mockImplementation(async (categoria) => ({
    usuario: "ana",
    categoria,
    productos: categoria === "Bebidas" ? ["Coca Cola", "Sprite"] : ["Leche"],
  }));
  vi.mocked(getForecast).mockResolvedValue(daily);
  vi.mocked(listSavedPredictions).mockResolvedValue({ usuario: "ana", total_lotes: 0, pagina_actual: 1, total_paginas: 0, lotes: [] });
});

afterEach(() => {
  act(() => useAuthStore.getState().clearSession());
  vi.clearAllMocks();
});

describe("PredictionsPage", () => {
  it("asks for nothing until the user presses calculate, even after choosing a category", async () => {
    const user = userEvent.setup();
    renderPage();
    await screen.findByRole("option", { name: "Lácteos" });

    await user.selectOptions(screen.getByRole("combobox", { name: "Alcance" }), "Lácteos");

    expect(getMonthlyForecast).not.toHaveBeenCalled();
    expect(getForecast).not.toHaveBeenCalled();
    expect(screen.getByText(/Consultarla no guarda nada/)).toBeInTheDocument();
  });

  it("draws history, projection, and the 95 % band for every category", async () => {
    const user = userEvent.setup();
    renderPage();

    await calculate(user);

    expect(await screen.findByRole("heading", { name: "Proyección de todas las categorías" })).toBeInTheDocument();
    expect(getMonthlyForecast).toHaveBeenCalledWith(undefined, undefined);
    expect(screen.getByText(/7 meses con solo tendencia.*a partir de 24 meses/)).toBeInTheDocument();
    const labels = lastChart().map((dataset) => dataset.label);
    expect(labels).toEqual(["Intervalo del 95 %", "", "Historial", "Proyección"]);
    expect(screen.getByText(/el valor real probablemente caerá dentro de esta zona/)).toBeInTheDocument();
    // The projection differs from the history by its dashes, not only by color.
    expect(lastChart()[2].borderDash).toBeUndefined();
    expect(lastChart()[3].borderDash).toEqual([6, 4]);
    const chartTable = screen.getByRole("table", { name: /^Datos de Monto: historial y proyección/ });
    expect(within(chartTable).getAllByRole("row").length).toBeGreaterThan(1);
    expect(lastChart()[3].data).toEqual([null, 9500, 10000, 12000, 8000, 8100, 9000, 9500, 9900]);
    expect(await screen.findByText("Mañana, todas las categorías")).toBeInTheDocument();
    expect(screen.getByText("$321.50")).toBeInTheDocument();
  });

  it("explains every forecast concept behind an info button", async () => {
    const user = userEvent.setup();
    vi.mocked(getMonthlyForecast).mockResolvedValueOnce(
      monthly({
        mes_parcial: { periodo: "2026-11", monto: 4200, cantidad: 40 },
        advertencias: ["Los meses 7 a 7 son extrapolación sin validar: su incertidumbre es mayor."],
        advertencia: "Los meses 7 a 7 son extrapolación sin validar: su incertidumbre es mayor.",
      }),
    );
    renderPage();

    await calculate(user);
    await screen.findByText("Toma esta proyección con cautela");
    await screen.findByText("Mañana, todas las categorías");
    await screen.findAllByText(/Rango probable/);

    for (const concept of [
      "intervalo del 95 %",
      "extrapolación",
      "tomar la proyección con cautela",
      "mes en curso",
      "tipo de modelo",
      "rango del día siguiente",
      "proyecciones guardadas",
    ]) {
      expect(screen.getAllByRole("button", { name: `Qué significa ${concept}` }).length).toBeGreaterThan(0);
    }
    expect(screen.getByText(/El punto hueco es el mes en curso, Nov 2026/)).toHaveTextContent("lleva $4,200.00 hasta ahora");

    const [interval] = screen.getAllByRole("button", { name: "Qué significa intervalo del 95 %" });
    interval.focus();
    await user.keyboard("{Enter}");
    expect(screen.getByRole("note")).toHaveTextContent(/de cada 100 meses, unos 95/);
    await user.keyboard("{Escape}");
    expect(screen.queryByRole("note")).not.toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Qué significa tomar la proyección con cautela" }));
    expect(screen.getByRole("note")).toHaveTextContent(/cargar más meses de ventas/);
  });

  it("explains extrapolation once in the monthly table", async () => {
    const user = userEvent.setup();
    renderPage();

    await calculate(user);

    const table = await screen.findByRole("table", { name: "Meses proyectados" });
    expect(within(table).getAllByRole("button", { name: "Qué significa extrapolación" })).toHaveLength(1);
    expect(within(table).getByRole("button", { name: "Qué significa intervalo del 95 %" })).toBeInTheDocument();
  });

  it("marks extrapolated months with a note", async () => {
    const user = userEvent.setup();
    renderPage();

    await calculate(user);

    expect(await screen.findByText(/Los rombos huecos y el trazo más fino marcan extrapolación/)).toBeInTheDocument();
    const rows = within(screen.getByRole("table", { name: "Meses proyectados" })).getAllByRole("row");
    expect(within(rows[7]).getByText("Extrapolación")).toBeInTheDocument();
    expect(within(rows[1]).queryByText("Extrapolación")).not.toBeInTheDocument();
  });

  it("shows the backend warning, and nothing when there is none", async () => {
    const user = userEvent.setup();
    vi.mocked(getMonthlyForecast).mockResolvedValueOnce(
      monthly({
        horizonte_aplicado: 6,
        advertencias: ["Con 12 meses completos la proyección es una tendencia.", "Los meses 7 a 12 son extrapolación sin validar."],
        advertencia: "Con 12 meses completos la proyección es una tendencia. Los meses 7 a 12 son extrapolación sin validar.",
      }),
    );
    renderPage();

    await calculate(user);

    expect(await screen.findByText("Toma esta proyección con cautela")).toBeInTheDocument();
    const reasons = screen.getAllByRole("listitem").map((item) => item.textContent);
    expect(reasons).toEqual(["Con 12 meses completos la proyección es una tendencia.", "Los meses 7 a 12 son extrapolación sin validar."]);
    expect(screen.getByText(/6 meses con solo tendencia/)).toBeInTheDocument();

    vi.mocked(getMonthlyForecast).mockResolvedValueOnce(monthly());
    await calculate(user);
    await waitFor(() => expect(screen.queryByText("Toma esta proyección con cautela")).not.toBeInTheDocument());
  });

  it("switches to units without asking the backend again", async () => {
    const user = userEvent.setup();
    renderPage();
    await calculate(user);
    await screen.findByRole("heading", { name: "Proyección de todas las categorías" });
    const calls = vi.mocked(getMonthlyForecast).mock.calls.length;

    await user.click(screen.getByRole("radio", { name: "Cantidad" }));

    expect(lastChart()[3].data[2]).toBe(100);
    expect(screen.getByRole("columnheader", { name: /Rango 95 % \(cantidad\)/ })).toBeInTheDocument();
    expect(getMonthlyForecast).toHaveBeenCalledTimes(calls);
  });

  it("opens the detail of the month chosen in the table", async () => {
    const user = userEvent.setup();
    renderPage();
    await calculate(user);
    expect(await screen.findByRole("region", { name: "Detalle de Nov 2026" })).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Dic 2026" }));

    const detail = screen.getByRole("region", { name: "Detalle de Dic 2026" });
    expect(detail).toHaveTextContent("$12,000.00");
    expect(screen.getAllByRole("row").find((row) => row.getAttribute("aria-selected") === "true")).toHaveTextContent("Dic 2026");
  });

  it("projects a category and warns when its model differs from the total", async () => {
    const user = userEvent.setup();
    vi.mocked(getMonthlyForecast).mockImplementation(async (categoria) =>
      categoria
        ? monthly({ categoria, horizonte_aplicado: 6, meses_observados: 12 })
        : monthly({ modelo: "tendencia_estacional", horizonte_aplicado: 12, meses_observados: 36 }),
    );
    renderPage();
    await screen.findByRole("option", { name: "Lácteos" });

    await user.selectOptions(screen.getByRole("combobox", { name: "Alcance" }), "Lácteos");
    await calculate(user);

    expect(await screen.findByRole("heading", { name: "Proyección de Lácteos" })).toBeInTheDocument();
    expect(getMonthlyForecast).toHaveBeenCalledWith("Lácteos", undefined);
    expect(await screen.findByText(/no suman\s+exactamente el total/)).toBeInTheDocument();
  });

  it("does not warn when the category and the total share a model", async () => {
    const user = userEvent.setup();
    renderPage();
    await screen.findByRole("option", { name: "Lácteos" });

    await user.selectOptions(screen.getByRole("combobox", { name: "Alcance" }), "Lácteos");
    await calculate(user);
    await screen.findByRole("heading", { name: "Proyección de Lácteos" });

    // The total is fetched to compare models; both share one here.
    await waitFor(() => expect(getMonthlyForecast).toHaveBeenCalledWith(undefined));
    expect(screen.queryByText(/no suman/)).not.toBeInTheDocument();
  });

  it("shows the backend detail when a category cannot be projected", async () => {
    const user = userEvent.setup();
    vi.mocked(getMonthlyForecast).mockRejectedValue(httpError(422, "No hay ventas de la categoría 'Lácteos' para proyectar."));
    renderPage();
    await screen.findByRole("option", { name: "Lácteos" });

    await user.selectOptions(screen.getByRole("combobox", { name: "Alcance" }), "Lácteos");
    await calculate(user);

    expect(await screen.findByText(/No hay ventas de la categoría 'Lácteos' para proyectar\./)).toHaveTextContent("Carga más ventas");
    expect(screen.queryByRole("button", { name: "Guardar proyección" })).not.toBeInTheDocument();
  });

  it("reports the next-day failure apart from the monthly projection", async () => {
    const user = userEvent.setup();
    vi.mocked(getForecast).mockRejectedValue(httpError(422, "Se necesitan al menos 2 días con ventas para proyectar."));
    renderPage();

    await calculate(user);

    expect(await screen.findByText(/Se necesitan al menos 2 días con ventas para proyectar\./)).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Proyección de todas las categorías" })).toBeInTheDocument();
  });

  it("saves the projection on request and refreshes the saved list", async () => {
    const user = userEvent.setup();
    vi.mocked(savePrediction).mockResolvedValue({ ...batch, puntos: Array(7).fill(batch.puntos[0] ?? null) });
    renderPage();
    expect(await screen.findByText("Aún no guardas proyecciones")).toBeInTheDocument();
    await screen.findByRole("option", { name: "Lácteos" });
    await user.selectOptions(screen.getByRole("combobox", { name: "Alcance" }), "Lácteos");
    await calculate(user);
    await screen.findByRole("heading", { name: "Proyección de Lácteos" });
    expect(savePrediction).not.toHaveBeenCalled();
    vi.mocked(listSavedPredictions).mockResolvedValue({ usuario: "ana", total_lotes: 1, pagina_actual: 1, total_paginas: 1, lotes: [batch] });

    await user.click(screen.getByRole("button", { name: "Guardar proyección" }));

    expect(savePrediction).toHaveBeenCalledWith("Lácteos", undefined);
    expect(await screen.findByText(/Proyección guardada: 7 meses/)).toBeInTheDocument();
    expect(await screen.findByText("Categoría: Lácteos")).toBeInTheDocument();
  });

  it("enables the product select only after a category and lists that category's products", async () => {
    const user = userEvent.setup();
    renderPage();
    await screen.findByRole("option", { name: "Bebidas" });
    const product = screen.getByRole("combobox", { name: "Producto" });
    expect(product).toBeDisabled();

    await user.selectOptions(screen.getByRole("combobox", { name: "Alcance" }), "Bebidas");
    await within(product).findByRole("option", { name: "Coca Cola" });
    await user.selectOptions(product, "Coca Cola");

    expect(product).toBeEnabled();
    expect(getProducts).toHaveBeenCalledWith("Bebidas");
    expect(getMonthlyForecast).not.toHaveBeenCalled();

    await user.selectOptions(screen.getByRole("combobox", { name: "Alcance" }), "Lácteos");
    expect(product).toHaveValue("");
  });

  it("projects a product and warns when its model differs from its category", async () => {
    const user = userEvent.setup();
    vi.mocked(getMonthlyForecast).mockImplementation(async (categoria, producto) =>
      producto
        ? monthly({ categoria: categoria ?? null, producto, horizonte_aplicado: 6, meses_observados: 12 })
        : monthly({ categoria: categoria ?? null, modelo: "tendencia_estacional", horizonte_aplicado: 12, meses_observados: 36 }),
    );
    vi.mocked(savePrediction).mockResolvedValue({ ...batch, categoria: "Bebidas", producto: "Coca Cola" });
    renderPage();
    await screen.findByRole("option", { name: "Bebidas" });
    await user.selectOptions(screen.getByRole("combobox", { name: "Alcance" }), "Bebidas");
    const product = screen.getByRole("combobox", { name: "Producto" });
    await within(product).findByRole("option", { name: "Coca Cola" });
    await user.selectOptions(product, "Coca Cola");

    await calculate(user);

    expect(await screen.findByRole("heading", { name: "Proyección de Coca Cola (Bebidas)" })).toBeInTheDocument();
    expect(getMonthlyForecast).toHaveBeenCalledWith("Bebidas", "Coca Cola");
    await waitFor(() => expect(getMonthlyForecast).toHaveBeenCalledWith("Bebidas"));
    expect(await screen.findByText(/no suman\s+exactamente la categoría/)).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Guardar proyección" }));
    expect(savePrediction).toHaveBeenCalledWith("Bebidas", "Coca Cola");
  });

  it("titles a saved product batch with its category and product", async () => {
    vi.mocked(listSavedPredictions).mockResolvedValue({
      usuario: "ana",
      total_lotes: 1,
      pagina_actual: 1,
      total_paginas: 1,
      lotes: [{ ...batch, categoria: "Bebidas", producto: "Coca Cola" }],
    });
    renderPage();

    expect(await screen.findByText("Bebidas · Coca Cola")).toBeInTheDocument();
  });

  it("explains a failed save", async () => {
    const user = userEvent.setup();
    vi.mocked(savePrediction).mockRejectedValue(httpError(500, "No se pudo guardar."));
    renderPage();
    await calculate(user);
    await screen.findByRole("heading", { name: "Proyección de todas las categorías" });

    await user.click(screen.getByRole("button", { name: "Guardar proyección" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("No se pudo guardar.");
  });

  it("never calls a projection a guarantee", async () => {
    const user = userEvent.setup();
    renderPage();
    await calculate(user);
    await screen.findByRole("heading", { name: "Proyección de todas las categorías" });

    expect(document.body.textContent?.toLowerCase()).not.toContain("garantía");
  });
});
