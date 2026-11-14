import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";
import { loginUser, resendVerification } from "../api/auth";
import { apiError } from "../test/apiError";
import { LoginPage } from "./LoginPage";

vi.mock("../api/auth", () => ({
  loginUser: vi.fn(),
  getCurrentUser: vi.fn(),
  resendVerification: vi.fn(),
}));

afterEach(() => vi.clearAllMocks());

async function submit(password = "StrongPass1") {
  const user = userEvent.setup();
  render(
    <MemoryRouter>
      <LoginPage />
    </MemoryRouter>,
  );
  await user.type(screen.getByLabelText("Correo electronico"), "ana@example.com");
  await user.type(screen.getByLabelText("Contraseña"), password);
  await user.click(screen.getByRole("button", { name: "Entrar" }));
  return user;
}

describe("LoginPage", () => {
  it("offers to resend the link when the e-mail is not verified", async () => {
    vi.mocked(loginUser).mockRejectedValue(apiError(403, "Verifica tu correo antes de iniciar sesión."));
    vi.mocked(resendVerification).mockResolvedValue({
      message: "Si el correo tiene una cuenta sin verificar, te enviamos un enlace nuevo.",
    });

    const user = await submit();

    expect(await screen.findByRole("alert")).toHaveTextContent("Verifica tu correo antes de iniciar sesión.");
    await user.click(screen.getByRole("button", { name: "Reenviar enlace" }));

    expect(resendVerification).toHaveBeenCalledWith("ana@example.com");
    expect(
      await screen.findByText("Si el correo tiene una cuenta sin verificar, te enviamos un enlace nuevo."),
    ).toBeInTheDocument();
  });

  it("does not offer a resend for wrong credentials", async () => {
    vi.mocked(loginUser).mockRejectedValue(apiError(401, "Credenciales invalidas."));

    await submit("Wrong1234");

    expect(await screen.findByRole("alert")).toHaveTextContent("Credenciales invalidas.");
    expect(screen.queryByRole("button", { name: "Reenviar enlace" })).not.toBeInTheDocument();
  });
});
