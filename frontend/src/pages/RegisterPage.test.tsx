import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";
import { registerUser } from "../api/auth";
import { apiError } from "../test/apiError";
import type { User } from "../types/api";
import { RegisterPage } from "./RegisterPage";

vi.mock("../api/auth", () => ({ registerUser: vi.fn() }));

afterEach(() => vi.clearAllMocks());

async function fillAndSubmit() {
  const user = userEvent.setup();
  render(
    <MemoryRouter>
      <RegisterPage />
    </MemoryRouter>,
  );
  await user.type(screen.getByLabelText("Nombre de usuario"), "ana");
  await user.type(screen.getByLabelText("Correo electronico"), "Ana@Example.com");
  await user.type(screen.getByLabelText("Contraseña"), "StrongPass1");
  await user.click(screen.getByRole("button", { name: "Crear cuenta" }));
}

describe("RegisterPage", () => {
  it("asks to open the e-mailed link instead of entering", async () => {
    vi.mocked(registerUser).mockResolvedValue({ correo_electronico: "ana@example.com" } as User);

    await fillAndSubmit();

    expect(await screen.findByText(/Te enviamos un enlace a ana@example.com/)).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Revisa tu correo" })).toBeInTheDocument();
    expect(registerUser).toHaveBeenCalledWith({
      nombre_usuario: "ana",
      correo_electronico: "ana@example.com",
      password: "StrongPass1",
    });
  });

  it("keeps the form and shows the backend error", async () => {
    vi.mocked(registerUser).mockRejectedValue(apiError(400, "El correo electronico ya se encuentra registrado."));

    await fillAndSubmit();

    expect(await screen.findByRole("alert")).toHaveTextContent("El correo electronico ya se encuentra registrado.");
    expect(screen.getByRole("button", { name: "Crear cuenta" })).toBeInTheDocument();
  });
});
