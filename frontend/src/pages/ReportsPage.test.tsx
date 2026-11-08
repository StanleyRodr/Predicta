import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { getCategoryStats } from "../api/analytics";
import { downloadReport } from "../api/reports";
import { useAuthStore } from "../stores/authStore";
import type { User } from "../types/api";
import { ReportsPage } from "./ReportsPage";

vi.mock("../api/analytics", () => ({ getCategoryStats: vi.fn() }));
vi.mock("../api/reports", () => ({ downloadReport: vi.fn(), reportErrorMessage: vi.fn() }));

function renderPage() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <ReportsPage />
    </QueryClientProvider>,
  );
}

function categories(names: string[]) {
  return {
    usuario: "ana",
    analisis_por_categoria: names.map((categoria) => ({ categoria, ingresos_totales: 10, cantidad_ventas: 1, ticket_promedio: 10 })),
  };
}

beforeEach(() => {
  act(() => useAuthStore.setState({ user: { id_usuario: 3 } as User }));
  vi.mocked(downloadReport).mockResolvedValue(undefined);
});

afterEach(() => {
  act(() => useAuthStore.getState().clearSession());
  vi.clearAllMocks();
});

describe("ReportsPage category report", () => {
  it("lists the user's categories and downloads the chosen one", async () => {
    vi.mocked(getCategoryStats).mockResolvedValue(categories(["Lácteos", "Abarrotes"]));
    const user = userEvent.setup();
    renderPage();

    const select = screen.getByRole("combobox", { name: "Categoría del reporte" });
    await screen.findByRole("option", { name: "Lácteos" });
    expect(within(select).getAllByRole("option").map((option) => option.textContent)).toEqual(["Abarrotes", "Lácteos"]);
    expect(select).toHaveValue("Abarrotes");

    await user.selectOptions(select, "Lácteos");
    await user.click(screen.getByRole("button", { name: "Descargar categoría" }));

    expect(getCategoryStats).toHaveBeenCalledWith({});
    expect(downloadReport).toHaveBeenCalledWith("/analytics/prediccion-categorias/L%C3%A1cteos", "reporte-categoria.pdf");
  });

  it("disables the category report when there are no categories", async () => {
    vi.mocked(getCategoryStats).mockResolvedValue(categories([]));
    renderPage();

    expect(await screen.findByText(/Todavía no hay categorías/)).toBeInTheDocument();
    expect(screen.getByRole("combobox", { name: "Categoría del reporte" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Descargar categoría" })).toBeDisabled();
  });
});
