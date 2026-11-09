import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { getCategoryStats, getProducts } from "../api/analytics";
import { getSalesHistory } from "../api/sales";
import { useAuthStore } from "../stores/authStore";
import type { User } from "../types/api";
import type { SalesHistoryResponse } from "../types/etl";
import { UploadPage } from "./UploadPage";

vi.mock("../api/analytics", () => ({ getCategoryStats: vi.fn(), getProducts: vi.fn() }));
vi.mock("../api/sales", () => ({ getSalesHistory: vi.fn() }));
vi.mock("../api/etl", () => ({ uploadSales: vi.fn(), clearSalesHistory: vi.fn() }));

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
