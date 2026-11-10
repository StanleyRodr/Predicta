import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { AxiosError, AxiosHeaders } from "axios";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { getCategoryStats } from "../api/analytics";
import { analyzeColumns, uploadSales } from "../api/etl";
import { getSalesHistory } from "../api/sales";
import { refreshSalesData } from "../lib/salesCache";
import { useAuthStore } from "../stores/authStore";
import type { User } from "../types/api";
import type { ColumnAnalysis, UploadResult } from "../types/etl";
import { UploadPage } from "./UploadPage";

vi.mock("../api/analytics", () => ({ getCategoryStats: vi.fn(), getProducts: vi.fn() }));
vi.mock("../api/sales", () => ({ getSalesHistory: vi.fn() }));
vi.mock("../api/etl", () => ({ analyzeColumns: vi.fn(), uploadSales: vi.fn(), clearSalesHistory: vi.fn() }));
vi.mock("../lib/salesCache", () => ({ refreshSalesData: vi.fn().mockResolvedValue(undefined) }));

const EMPTY = { columna: null, origen: null, candidatos: [] };

function analysis(columnas: string[], producto: string, monto: string, fecha: string): ColumnAnalysis {
  return {
    columnas,
    muestra: [],
    propuesta: {
      producto: { columna: producto, origen: "sinonimo", candidatos: [] },
      categoria: EMPTY,
      monto: { columna: monto, origen: "sinonimo", candidatos: [] },
      precio_unitario: EMPTY,
      cantidad: EMPTY,
      fecha: { columna: fecha, origen: "sinonimo", candidatos: [] },
    },
    faltantes: [],
  };
}

const IOWA = analysis(["im_desc", "sales_dollars", "ordered_on"], "im_desc", "sales_dollars", "ordered_on");
const OTHER = analysis(["item", "total", "fecha"], "item", "total", "fecha");

function result(leidos: number): UploadResult {
  return { message: "ok", registros_leidos: leidos, registros_cargados: leidos, filas_rechazadas: 0, errores: [] };
}

function conflict(): AxiosError {
  const config = { headers: new AxiosHeaders() };
  return new AxiosError("dup", undefined, config, undefined, {
    status: 409,
    statusText: "Conflict",
    headers: {},
    config,
    data: { detail: "Este archivo ya fue cargado." },
  });
}

function csv(name: string): File {
  return new File(["data"], name, { type: "text/csv" });
}

function renderPage() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <UploadPage />
    </QueryClientProvider>,
  );
}

function chooseFiles(files: File[]) {
  fireEvent.change(screen.getByLabelText("Seleccionar archivo"), { target: { files } });
}

function uploadedNames() {
  return vi.mocked(uploadSales).mock.calls.map(([file]) => file.name);
}

beforeEach(() => {
  act(() => useAuthStore.setState({ user: { id_usuario: 3 } as User }));
  vi.mocked(getCategoryStats).mockResolvedValue({ usuario: "ana", analisis_por_categoria: [] });
  vi.mocked(getSalesHistory).mockResolvedValue({ usuario: "ana", total_registros: 0, pagina_actual: 1, total_paginas: 0, registros: [] });
});

afterEach(() => {
  act(() => useAuthStore.getState().clearSession());
  vi.clearAllMocks();
});

describe("UploadPage with several files", () => {
  it("analyzes in name order, shows one mapping for shared headers and uploads every file with it", async () => {
    const user = userEvent.setup();
    vi.mocked(analyzeColumns).mockResolvedValue(IOWA);
    vi.mocked(uploadSales).mockResolvedValue(result(10));
    renderPage();

    chooseFiles([csv("iowa_2014.csv"), csv("iowa_2012.csv"), csv("iowa_2013.csv")]);

    const panel = await screen.findByRole("region", { name: "Mapeo para 3 archivos: iowa_2012.csv … iowa_2014.csv" });
    expect(vi.mocked(analyzeColumns).mock.calls.map(([file]) => file.name)).toEqual(["iowa_2012.csv", "iowa_2013.csv", "iowa_2014.csv"]);
    expect(screen.getAllByRole("group", { name: "Mapeo de columnas" })).toHaveLength(1);

    await user.selectOptions(within(panel).getByRole("combobox", { name: "Columna para Producto" }), "ordered_on");
    await user.selectOptions(within(panel).getByRole("combobox", { name: "Columna para Fecha" }), "im_desc");
    await user.click(screen.getByRole("button", { name: "Cargar ventas" }));

    await screen.findByText("Carga terminada: 3 archivos procesados");
    expect(uploadedNames()).toEqual(["iowa_2012.csv", "iowa_2013.csv", "iowa_2014.csv"]);
    const corrected = { producto: "ordered_on", monto: "sales_dollars", fecha: "im_desc" };
    expect(vi.mocked(uploadSales).mock.calls.map(([, mapeo]) => mapeo)).toEqual([corrected, corrected, corrected]);
    expect(within(screen.getByRole("row", { name: /^Total/ })).getByText("3 de 3 cargados")).toBeInTheDocument();
  });

  it("gives a file with different headers its own mapping", async () => {
    const user = userEvent.setup();
    vi.mocked(analyzeColumns).mockImplementation(async (file) => (file.name.startsWith("otro") ? OTHER : IOWA));
    vi.mocked(uploadSales).mockResolvedValue(result(5));
    renderPage();

    chooseFiles([csv("iowa_2012.csv"), csv("otro.csv"), csv("iowa_2013.csv")]);

    await screen.findByRole("region", { name: "Mapeo para 2 archivos: iowa_2012.csv … iowa_2013.csv" });
    expect(screen.getByRole("region", { name: "Mapeo para 1 archivo: otro.csv" })).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Cargar ventas" }));

    await screen.findByText("Carga terminada: 3 archivos procesados");
    const mappingByFile = Object.fromEntries(vi.mocked(uploadSales).mock.calls.map(([file, mapeo]) => [file.name, mapeo]));
    expect(mappingByFile).toEqual({
      "iowa_2012.csv": { producto: "im_desc", monto: "sales_dollars", fecha: "ordered_on" },
      "iowa_2013.csv": { producto: "im_desc", monto: "sales_dollars", fecha: "ordered_on" },
      "otro.csv": { producto: "item", monto: "total", fecha: "fecha" },
    });
  });

  it("keeps going after a duplicate and refreshes the sales data once", async () => {
    const user = userEvent.setup();
    vi.mocked(analyzeColumns).mockResolvedValue(IOWA);
    vi.mocked(uploadSales)
      .mockResolvedValueOnce(result(10))
      .mockRejectedValueOnce(conflict())
      .mockResolvedValueOnce(result(20));
    renderPage();

    chooseFiles([csv("iowa_2012.csv"), csv("iowa_2013.csv"), csv("iowa_2014.csv")]);
    await user.click(await screen.findByRole("button", { name: "Cargar ventas" }));

    await screen.findByText("Carga terminada: 3 archivos procesados");
    expect(uploadedNames()).toEqual(["iowa_2012.csv", "iowa_2013.csv", "iowa_2014.csv"]);
    const duplicate = within(screen.getByRole("row", { name: /iowa_2013\.csv/ }));
    expect(duplicate.getByText("Ya cargado")).toBeInTheDocument();
    expect(duplicate.getByText("Este archivo ya fue cargado.")).toBeInTheDocument();
    expect(within(screen.getByRole("row", { name: /^Total/ })).getByText("2 de 3 cargados")).toBeInTheDocument();
    expect(refreshSalesData).toHaveBeenCalledTimes(1);
  });

  it("lists an unsupported file without analyzing or uploading it", async () => {
    const user = userEvent.setup();
    vi.mocked(analyzeColumns).mockResolvedValue(IOWA);
    vi.mocked(uploadSales).mockResolvedValue(result(10));
    renderPage();

    chooseFiles([csv("iowa_2012.csv"), new File(["x"], "notas.txt"), csv("iowa_2013.csv")]);
    await user.click(await screen.findByRole("button", { name: "Cargar ventas" }));

    await screen.findByText("Carga terminada: 2 archivos procesados");
    expect(vi.mocked(analyzeColumns).mock.calls.map(([file]) => file.name)).not.toContain("notas.txt");
    expect(uploadedNames()).toEqual(["iowa_2012.csv", "iowa_2013.csv"]);
    expect(within(screen.getByRole("row", { name: /notas\.txt/ })).getByText("No válido")).toBeInTheDocument();
  });

  it("blocks the upload while a group mapping has a problem", async () => {
    const user = userEvent.setup();
    vi.mocked(analyzeColumns).mockResolvedValue(IOWA);
    renderPage();

    chooseFiles([csv("iowa_2012.csv"), csv("iowa_2013.csv")]);
    const panel = await screen.findByRole("region", { name: /Mapeo para 2 archivos/ });
    await user.selectOptions(within(panel).getByRole("combobox", { name: "Columna para Fecha" }), "");

    expect(screen.getByRole("button", { name: "Cargar ventas" })).toBeDisabled();
    expect(within(panel).getByText("Falta asignar: Fecha.")).toBeInTheDocument();
    expect(uploadSales).not.toHaveBeenCalled();
  });

  it("ignores the analyses of a selection the user already replaced", async () => {
    let finishFirst: (value: ColumnAnalysis) => void = () => {};
    vi.mocked(analyzeColumns)
      .mockImplementationOnce(() => new Promise((resolve) => (finishFirst = resolve)))
      .mockResolvedValue(OTHER);
    renderPage();

    chooseFiles([csv("iowa_2012.csv"), csv("iowa_2013.csv")]);
    await waitFor(() => expect(analyzeColumns).toHaveBeenCalledTimes(1));
    chooseFiles([csv("otro_1.csv"), csv("otro_2.csv")]);
    await screen.findByRole("region", { name: "Mapeo para 2 archivos: otro_1.csv … otro_2.csv" });
    await act(async () => finishFirst(IOWA));

    expect(screen.queryByRole("row", { name: /iowa_2012\.csv/ })).not.toBeInTheDocument();
    expect(screen.queryByRole("region", { name: /iowa/ })).not.toBeInTheDocument();
    expect(vi.mocked(analyzeColumns).mock.calls.map(([file]) => file.name)).not.toContain("iowa_2013.csv");
  });
});
