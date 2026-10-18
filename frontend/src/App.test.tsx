import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { describe, expect, it } from "vitest";
import App from "./App";

function renderApp() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <App />
    </QueryClientProvider>,
  );
}

describe("Predicta foundation", () => {
  it("renders the Spanish foundation screen", () => {
    renderApp();

    expect(screen.getByText("Tus ventas, con siguiente movimiento.")).toBeInTheDocument();
    expect(screen.getByText("Sube un archivo para activar tus métricas.")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Entrar al panel" })).toHaveAttribute("href", "/login");
    expect(screen.getByRole("link", { name: "Crear cuenta" })).toHaveAttribute("href", "/register");
    expect(screen.getByRole("link", { name: "Cargar ventas" })).toHaveAttribute("href", "/upload");
  });
});
