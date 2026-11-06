import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { getForecast } from "../../api/forecast";
import { PredictionsPage } from "../../pages/PredictionsPage";
import { useAuthStore } from "../../stores/authStore";
import type { User } from "../../types/api";
import type { ForecastResponse } from "../../types/forecast";
import { SessionCacheGuard } from "./SessionCacheGuard";

vi.mock("../../api/forecast", () => ({ getForecast: vi.fn() }));

const metrics = { r2: 0.5, mape: 10, rmse: 5 };
const forecast: ForecastResponse = {
  usuario: "usuario-a",
  proxima_fecha: "2026-01-15",
  monto_predicho: 4321.5,
  cantidad_predicha: 12,
  monto_original_crudo: 4321.5,
  intervalos_prediccion: {
    monto: { inferior: 4000, superior: 4600 },
    cantidad: { inferior: 10, superior: 14 },
  },
  metricas: { monto: metrics, cantidad: metrics },
  mensaje: "Prediccion ajustada.",
};

function user(id: number): User {
  return { id_usuario: id } as User;
}

afterEach(() => {
  act(() => useAuthStore.getState().clearSession());
  vi.clearAllMocks();
});

describe("SessionCacheGuard", () => {
  it("does not show a forecast from the previous user", async () => {
    vi.mocked(getForecast).mockResolvedValue(forecast);
    act(() => useAuthStore.getState().setSession("token-a", user(1)));
    render(
      <QueryClientProvider client={new QueryClient()}>
        <SessionCacheGuard />
        <PredictionsPage />
      </QueryClientProvider>,
    );

    await userEvent.click(screen.getByRole("button", { name: "Calcular prediccion" }));
    expect(await screen.findByText("$4,321.50")).toBeInTheDocument();

    act(() => useAuthStore.getState().clearSession());
    act(() => useAuthStore.getState().setSession("token-b", user(2)));

    expect(screen.queryByText("$4,321.50")).not.toBeInTheDocument();
  });

  it("clears the cache when the session ends", () => {
    const queryClient = new QueryClient();
    act(() => useAuthStore.getState().setSession("token-a", user(1)));
    render(
      <QueryClientProvider client={queryClient}>
        <SessionCacheGuard />
      </QueryClientProvider>,
    );
    queryClient.setQueryData(["forecast", 1], forecast);

    act(() => useAuthStore.getState().clearSession());

    expect(queryClient.getQueryCache().getAll()).toHaveLength(0);
  });

  it("keeps queries started by a first login", () => {
    const queryClient = new QueryClient();
    render(
      <QueryClientProvider client={queryClient}>
        <SessionCacheGuard />
      </QueryClientProvider>,
    );
    queryClient.setQueryData(["forecast", 1], forecast);

    act(() => useAuthStore.getState().setSession("token-a", user(1)));

    expect(queryClient.getQueryData(["forecast", 1])).toEqual(forecast);
  });
});
