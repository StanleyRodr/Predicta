import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { AxiosError, AxiosHeaders } from "axios";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { getForecast } from "../api/forecast";
import { useAuthStore } from "../stores/authStore";
import type { User } from "../types/api";
import { PredictionsPage } from "./PredictionsPage";

vi.mock("../api/forecast", () => ({ getForecast: vi.fn() }));

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
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <PredictionsPage />
    </QueryClientProvider>,
  );
}

beforeEach(() => {
  act(() => useAuthStore.setState({ user: { id_usuario: 3 } as User }));
});

afterEach(() => {
  act(() => useAuthStore.getState().clearSession());
  vi.clearAllMocks();
});

describe("PredictionsPage", () => {
  it("shows the backend detail when the history is too short", async () => {
    const user = userEvent.setup();
    vi.mocked(getForecast).mockRejectedValue(httpError(422, "Se necesitan al menos 2 días con ventas para proyectar."));
    renderPage();

    await user.click(screen.getByRole("button", { name: /Calcular/ }));

    const alert = await screen.findByText(/Se necesitan al menos 2 días con ventas para proyectar\./);
    expect(alert).toHaveTextContent("Carga más días de ventas");
    expect(getForecast).toHaveBeenCalledTimes(1);
  });

  it("reports other failures as errors", async () => {
    const user = userEvent.setup();
    vi.mocked(getForecast).mockRejectedValue(httpError(500, "No se pudo calcular."));
    renderPage();

    await user.click(screen.getByRole("button", { name: /Calcular/ }));

    expect(await screen.findByText("No se pudo calcular.")).toBeInTheDocument();
    expect(screen.queryByText(/Carga más días de ventas/)).not.toBeInTheDocument();
  });
});
