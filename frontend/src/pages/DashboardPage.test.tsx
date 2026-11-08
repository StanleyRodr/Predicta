import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { getCategoryStats, getGlobalStats, getSalesSeries } from "../api/analytics";
import { useAuthStore } from "../stores/authStore";
import type { User } from "../types/api";
import type { SeriesParams, SeriesPoint, SeriesResponse } from "../types/analytics";
import { DashboardPage } from "./DashboardPage";

vi.mock("../api/analytics", () => ({
  getGlobalStats: vi.fn(),
  getCategoryStats: vi.fn(),
  getSalesSeries: vi.fn(),
}));

interface CapturedDataset {
  label: string;
  hidden?: boolean;
  data: (number | null)[];
}

const charts = vi.hoisted(() => ({ last: [] as { datasets: CapturedDataset[] }[] }));

vi.mock("react-chartjs-2", () => {
  const Chart = ({ data }: { data: { datasets: CapturedDataset[] } }) => {
    charts.last.push(data);
    return null;
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
    ingresos: 100 * mes,
    cantidad: mes,
    ventas_realizadas: 1,
    ...extra,
  };
}

function seriesResponse(params: SeriesParams): SeriesResponse {
  const puntos =
    params.granularidad === "dia"
      ? [point(2025, 3, { dia: 4, periodo: "2025-03-04" })]
      : params.por_categoria
        ? [point(2025, 1, { categoria: "Bebidas" }), point(2025, 1, { categoria: "Lácteos" })]
        : [point(2024, 11), point(2024, 12), point(2025, 1), point(2025, 3)];
  return {
    usuario: "ana",
    granularidad: params.granularidad ?? "mes",
    categoria: params.categoria ?? null,
    por_categoria: Boolean(params.por_categoria),
    puntos,
  };
}

function renderPage() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <DashboardPage />
    </QueryClientProvider>,
  );
}

function seriesCalls(): SeriesParams[] {
  return vi.mocked(getSalesSeries).mock.calls.map(([params]) => params);
}

beforeEach(() => {
  charts.last = [];
  act(() => useAuthStore.setState({ user: { id_usuario: 7 } as User }));
  vi.mocked(getGlobalStats).mockResolvedValue({
    usuario: "ana",
    metricas_globales: { total_ingresos: 1000, cantidad_operaciones: 4, ticket_promedio: 250, venta_mas_alta: 400 },
  });
  vi.mocked(getCategoryStats).mockResolvedValue({
    usuario: "ana",
    analisis_por_categoria: [
      { categoria: "Lácteos", ingresos_totales: 300, cantidad_ventas: 2, ticket_promedio: 150 },
      { categoria: "Bebidas", ingresos_totales: 700, cantidad_ventas: 2, ticket_promedio: 350 },
    ],
  });
  vi.mocked(getSalesSeries).mockImplementation(async (params) => seriesResponse(params));
});

afterEach(() => {
  act(() => useAuthStore.getState().clearSession());
  vi.clearAllMocks();
});

describe("DashboardPage", () => {
  it("opens on the overlaid years of every category", async () => {
    renderPage();

    expect(await screen.findByRole("img", { name: /Monto por mes, un año por línea/ })).toBeInTheDocument();
    expect(seriesCalls()).toEqual([{ granularidad: "mes", categoria: undefined }]);
    await waitFor(() => expect(charts.last.at(-1)?.datasets.map((dataset) => dataset.label)).toEqual(["2024", "2025"]));
  });

  it("isolates one year without dropping the others from the legend", async () => {
    const user = userEvent.setup();
    renderPage();
    await screen.findByRole("img", { name: /un año por línea/ });

    await user.selectOptions(screen.getByRole("combobox", { name: "Año" }), "2025");

    const datasets = charts.last.at(-1)?.datasets ?? [];
    expect(datasets.map((dataset) => [dataset.label, Boolean(dataset.hidden)])).toEqual([
      ["2024", true],
      ["2025", false],
    ]);
  });

  it("switches the measure to quantity", async () => {
    const user = userEvent.setup();
    renderPage();
    await screen.findByRole("img", { name: /un año por línea/ });

    await user.click(screen.getByRole("radio", { name: "Cantidad" }));

    expect(await screen.findByRole("img", { name: /Cantidad por mes/ })).toBeInTheDocument();
    expect(charts.last.at(-1)?.datasets[1].data[0]).toBe(1);
  });

  it("requests a category with its own query key", async () => {
    const user = userEvent.setup();
    renderPage();
    await screen.findByRole("img", { name: /un año por línea/ });

    await user.selectOptions(screen.getByRole("combobox", { name: "Categoría" }), "Lácteos");

    await waitFor(() => expect(seriesCalls()).toContainEqual({ granularidad: "mes", categoria: "Lácteos" }));
    expect(screen.getByText(/Lácteos\. Una línea por año/)).toBeInTheDocument();
  });

  it("compares categories and defaults to the top-selling one", async () => {
    const user = userEvent.setup();
    renderPage();
    await screen.findByRole("img", { name: /un año por línea/ });

    await user.click(screen.getByRole("radio", { name: "Por categoría" }));

    await waitFor(() => {
      expect(seriesCalls()).toContainEqual({ granularidad: "mes", categoria: "Bebidas" });
      expect(seriesCalls()).toContainEqual({ granularidad: "mes", por_categoria: true });
    });
    expect(await screen.findByRole("img", { name: /mensual por categoría/ })).toBeInTheDocument();
    expect(screen.getByRole("combobox", { name: "Categoría" })).toHaveValue("Bebidas");
  });

  it("does not carry the category view's default category into other views", async () => {
    const user = userEvent.setup();
    renderPage();
    await screen.findByRole("img", { name: /un año por línea/ });

    await user.click(screen.getByRole("radio", { name: "Por categoría" }));
    await screen.findByRole("img", { name: /mensual por categoría/ });
    await user.click(screen.getByRole("radio", { name: "Por mes" }));

    expect(await screen.findByText(/Todas las categorías. Elige una barra/)).toBeInTheDocument();
    expect(screen.getByRole("combobox", { name: "Categoría" })).toHaveValue("");
  });

  it("opens the month view on the last month with sales and asks for its days", async () => {
    const user = userEvent.setup();
    renderPage();
    await screen.findByRole("img", { name: /un año por línea/ });

    await user.click(screen.getByRole("radio", { name: "Por mes" }));

    expect(await screen.findByText("Detalle diario: Marzo 2025")).toBeInTheDocument();
    await waitFor(() =>
      expect(seriesCalls()).toContainEqual({
        granularidad: "dia",
        categoria: undefined,
        fecha_desde: "2025-03-01",
        fecha_hasta: "2025-03-31",
      }),
    );

    await user.selectOptions(screen.getByRole("combobox", { name: "Mes" }), "1");
    await waitFor(() =>
      expect(seriesCalls()).toContainEqual({
        granularidad: "dia",
        categoria: undefined,
        fecha_desde: "2025-01-01",
        fecha_hasta: "2025-01-31",
      }),
    );
  });

  it("keeps the full monthly history as a secondary view", async () => {
    const user = userEvent.setup();
    renderPage();
    await screen.findByRole("img", { name: /un año por línea/ });

    await user.click(screen.getByRole("radio", { name: "Historial completo" }));

    expect(await screen.findByRole("img", { name: /mensual de todo el historial/ })).toBeInTheDocument();
    const values = charts.last.at(-1)?.datasets[0].data;
    expect(values).toEqual([1100, 1200, 100, null, 300]);
  });

  it("sends the active date range to the cards and the charts", async () => {
    const user = userEvent.setup();
    renderPage();
    await screen.findByRole("img", { name: /un año por línea/ });

    await user.type(screen.getByLabelText("Fecha desde"), "2025-01-01");
    await user.click(screen.getByRole("button", { name: "Aplicar filtro" }));

    const range = { fecha_desde: "2025-01-01", fecha_hasta: undefined };
    await waitFor(() => {
      expect(getGlobalStats).toHaveBeenLastCalledWith(range);
      expect(seriesCalls()).toContainEqual({ granularidad: "mes", categoria: undefined, ...range });
    });
    expect(screen.getByText(/Rango activo:/)).toHaveTextContent("Aplica a las tarjetas y a todos los gráficos.");
  });
});
