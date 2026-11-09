import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { getCategoryStats, getProducts } from "../api/analytics";
import { analyzeColumns, uploadSales } from "../api/etl";
import { getSalesHistory } from "../api/sales";
import { useAuthStore } from "../stores/authStore";
import type { User } from "../types/api";
import type { ColumnAnalysis, SalesHistoryResponse } from "../types/etl";
import { UploadPage } from "./UploadPage";

vi.mock("../api/analytics", () => ({ getCategoryStats: vi.fn(), getProducts: vi.fn() }));
vi.mock("../api/sales", () => ({ getSalesHistory: vi.fn() }));
vi.mock("../api/etl", () => ({ analyzeColumns: vi.fn(), uploadSales: vi.fn(), clearSalesHistory: vi.fn() }));

function history(total: number): SalesHistoryResponse {
  return {
    usuario: "ana",
    total_registros: total,
    pagina_actual: 1,
    total_paginas: Math.ceil(total / 10),
    registros: [{ id: 1, producto: "Coca Cola", monto: 10, categoria: "Bebidas", fecha: "2026-01-05 00:00:00" }],
  };
}

function renderPage() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <UploadPage />
    </QueryClientProvider>,
  );
}

function lastHistoryCall() {
  return vi.mocked(getSalesHistory).mock.calls.at(-1);
}

beforeEach(() => {
  act(() => useAuthStore.setState({ user: { id_usuario: 3 } as User }));
  vi.mocked(getCategoryStats).mockResolvedValue({
    usuario: "ana",
    analisis_por_categoria: [
      { categoria: "Lácteos", ingresos_totales: 300, cantidad_ventas: 3, ticket_promedio: 100 },
      { categoria: "Bebidas", ingresos_totales: 900, cantidad_ventas: 3, ticket_promedio: 300 },
    ],
  });
  vi.mocked(getProducts).mockResolvedValue({ usuario: "ana", categoria: "Bebidas", productos: ["Coca Cola", "Sprite"] });
  vi.mocked(getSalesHistory).mockResolvedValue(history(30));
});

afterEach(() => {
  act(() => useAuthStore.getState().clearSession());
  vi.clearAllMocks();
});

describe("UploadPage sales history filters", () => {
  it("keeps the product select disabled until a category is chosen", async () => {
    renderPage();
    await screen.findByRole("option", { name: "Bebidas" });

    expect(screen.getByRole("combobox", { name: "Producto" })).toBeDisabled();
    expect(getProducts).not.toHaveBeenCalled();
    expect(lastHistoryCall()).toEqual([0, 10, "", ""]);
  });

  it("filters by category and product and goes back to page 1 on every change", async () => {
    const user = userEvent.setup();
    renderPage();
    await user.click(await screen.findByRole("button", { name: /siguiente/i }));
    await waitFor(() => expect(lastHistoryCall()).toEqual([10, 10, "", ""]));

    await user.selectOptions(screen.getByRole("combobox", { name: "Categoría" }), "Bebidas");
    await waitFor(() => expect(lastHistoryCall()).toEqual([0, 10, "Bebidas", ""]));

    const product = screen.getByRole("combobox", { name: "Producto" });
    await within(product).findByRole("option", { name: "Coca Cola" });
    await user.selectOptions(product, "Coca Cola");

    await waitFor(() => expect(lastHistoryCall()).toEqual([0, 10, "Bebidas", "Coca Cola"]));
    expect(getProducts).toHaveBeenCalledWith("Bebidas");
  });
});

const EMPTY = { columna: null, origen: null, candidatos: [] };

function analysis(columnas: string[], propuesta: Partial<ColumnAnalysis["propuesta"]>): ColumnAnalysis {
  return {
    columnas,
    muestra: [],
    propuesta: { producto: EMPTY, categoria: EMPTY, monto: EMPTY, precio_unitario: EMPTY, cantidad: EMPTY, fecha: EMPTY, ...propuesta },
    faltantes: [],
  };
}

const MAPPED = analysis(["item", "total", "importe", "fecha"], {
  producto: { columna: "item", origen: "sinonimo", candidatos: [] },
  monto: { columna: "total", origen: "sinonimo", candidatos: [] },
  fecha: { columna: "fecha", origen: "exacto", candidatos: [] },
});

function chooseFile(name = "ventas.csv") {
  const file = new File(["data"], name, { type: "text/csv" });
  fireEvent.change(screen.getByLabelText("Seleccionar archivo"), { target: { files: [file] } });
  return file;
}

async function mappingPanel() {
  return within(await screen.findByRole("group", { name: "Mapeo de columnas" }));
}

describe("UploadPage column mapping", () => {
  it("analyzes the chosen file and uploads the mapping the user corrected", async () => {
    const user = userEvent.setup();
    vi.mocked(analyzeColumns).mockResolvedValue(MAPPED);
    vi.mocked(uploadSales).mockResolvedValue({ message: "ok", registros_leidos: 1, registros_cargados: 1, filas_rechazadas: 0, errores: [] });
    renderPage();

    const file = chooseFile();
    await waitFor(() => expect(analyzeColumns).toHaveBeenCalledWith(file));
    const amount = await (await mappingPanel()).findByRole("combobox", { name: "Columna para Monto" });
    expect(amount).toHaveValue("total");

    await user.selectOptions(amount, "importe");
    await user.click(screen.getByRole("button", { name: "Cargar ventas" }));

    await waitFor(() => expect(uploadSales).toHaveBeenCalledWith(file, { producto: "item", monto: "importe", fecha: "fecha" }));
  });

  it("blocks the upload while a required role is missing or a column repeats", async () => {
    const user = userEvent.setup();
    vi.mocked(analyzeColumns).mockResolvedValue(MAPPED);
    renderPage();
    chooseFile();
    const date = await (await mappingPanel()).findByRole("combobox", { name: "Columna para Fecha" });

    await user.selectOptions(date, "");
    expect(screen.getByRole("button", { name: "Cargar ventas" })).toBeDisabled();
    expect(screen.getByText("Falta asignar: Fecha.")).toBeInTheDocument();

    await user.selectOptions(date, "item");
    expect(screen.getByRole("button", { name: "Cargar ventas" })).toBeDisabled();
    expect(screen.getByText("La columna item está asignada a dos roles.")).toBeInTheDocument();
  });

  it("shows the analysis error and keeps the upload disabled", async () => {
    vi.mocked(analyzeColumns).mockRejectedValue(new Error("boom"));
    renderPage();
    chooseFile();

    expect(await screen.findByText("No se pudo analizar el archivo.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Cargar ventas" })).toBeDisabled();
    expect(screen.queryByRole("group", { name: "Mapeo de columnas" })).not.toBeInTheDocument();
  });

  it("ignores a late analysis of a file the user already replaced", async () => {
    let finishFirst: (value: ColumnAnalysis) => void = () => {};
    const second = analysis(["producto", "monto", "fecha"], {
      producto: { columna: "producto", origen: "exacto", candidatos: [] },
      monto: { columna: "monto", origen: "exacto", candidatos: [] },
      fecha: { columna: "fecha", origen: "exacto", candidatos: [] },
    });
    vi.mocked(analyzeColumns)
      .mockImplementationOnce(() => new Promise((resolve) => (finishFirst = resolve)))
      .mockResolvedValueOnce(second);
    renderPage();

    chooseFile("primero.csv");
    chooseFile("segundo.csv");
    const product = await (await mappingPanel()).findByRole("combobox", { name: "Columna para Producto" });
    await act(async () => finishFirst(MAPPED));

    expect(product).toHaveValue("producto");
    expect(within(product).queryByRole("option", { name: "item" })).not.toBeInTheDocument();
  });
});
