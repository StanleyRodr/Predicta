import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";
import { forgotPassword } from "../api/auth";
import { ForgotPasswordPage } from "./ForgotPasswordPage";

vi.mock("../api/auth", () => ({ forgotPassword: vi.fn() }));

const ANSWER = "Si el correo tiene una cuenta, te enviamos un enlace para elegir una contraseña nueva.";

afterEach(() => vi.clearAllMocks());

async function ask(email: string) {
  const user = userEvent.setup();
  render(
    <MemoryRouter>
      <ForgotPasswordPage />
    </MemoryRouter>,
  );
  await user.type(screen.getByLabelText("Correo electronico"), email);
  await user.click(screen.getByRole("button", { name: "Enviar enlace" }));
}

describe("ForgotPasswordPage", () => {
  it.each(["ana@example.com", "nadie@example.com"])("shows the backend's same answer for %s", async (email) => {
    vi.mocked(forgotPassword).mockResolvedValue({ message: ANSWER });

    await ask(email);

    expect(await screen.findByText(ANSWER)).toBeInTheDocument();
    expect(forgotPassword).toHaveBeenCalledWith(email);
    expect(screen.getByRole("link", { name: "Volver a iniciar sesión" })).toHaveAttribute("href", "/login");
  });

  it("does not call the API with an invalid e-mail", async () => {
    // The browser's type="email" check or Zod stops the submit first.
    await ask("no-es-correo");

    expect(forgotPassword).not.toHaveBeenCalled();
    expect(screen.getByRole("button", { name: "Enviar enlace" })).toBeInTheDocument();
  });
});
