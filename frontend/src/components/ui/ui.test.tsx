import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import { Button } from "./Button";
import { EmptyState } from "./EmptyState";
import { Input } from "./Input";

describe("base UI components", () => {
  it("supports disabled buttons and keyboard focus", async () => {
    const user = userEvent.setup();
    render(
      <>
        <Button>Entrar</Button>
        <Button disabled>Guardar</Button>
      </>,
    );

    expect(screen.getByRole("button", { name: "Guardar" })).toBeDisabled();
    await user.tab();
    expect(screen.getByRole("button", { name: "Entrar" })).toHaveFocus();
  });

  it("marks invalid inputs with their public error message", () => {
    render(<Input id="correo" label="Correo" error="Correo invalido" />);

    expect(screen.getByRole("textbox")).toHaveAttribute("aria-invalid", "true");
    expect(screen.getByText("Correo invalido")).toBeInTheDocument();
  });

  it("renders actionable empty states", () => {
    render(
      <EmptyState
        action={<Button>Subir archivo</Button>}
        description="Carga ventas para comenzar."
        title="Sin datos"
      />,
    );

    expect(screen.getByRole("heading", { name: "Sin datos" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Subir archivo" })).toBeInTheDocument();
  });
});
