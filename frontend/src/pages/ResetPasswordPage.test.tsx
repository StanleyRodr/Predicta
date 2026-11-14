import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";
import { resetPassword } from "../api/auth";
import { MISSING_TOKEN } from "../lib/linkToken";
import { apiError } from "../test/apiError";
import { ResetPasswordPage } from "./ResetPasswordPage";

vi.mock("../api/auth", () => ({ resetPassword: vi.fn() }));

function openLink(hash: string) {
  window.history.replaceState(null, "", `/restablecer-contrasena${hash}`);
  render(
    <MemoryRouter>
      <ResetPasswordPage />
    </MemoryRouter>,
  );
  return userEvent.setup();
}

async function fill(user: ReturnType<typeof userEvent.setup>, nueva: string, confirmacion = nueva) {
  await user.type(screen.getByLabelText("Contraseña nueva"), nueva);
  await user.type(screen.getByLabelText("Repite la contraseña nueva"), confirmacion);
  await user.click(screen.getByRole("button", { name: "Guardar contraseña" }));
}

afterEach(() => {
  vi.clearAllMocks();
  window.history.replaceState(null, "", "/");
});

describe("ResetPasswordPage", () => {
  it("sends the token with the new password and shows the success", async () => {
    vi.mocked(resetPassword).mockResolvedValue({ message: "Contraseña actualizada. Ya puedes iniciar sesión." });
    const user = openLink("#token=abc_123");

    expect(window.location.hash).toBe("");
    await fill(user, "OtraClave9");

    expect(resetPassword).toHaveBeenCalledWith("abc_123", "OtraClave9");
    expect(await screen.findByText("Contraseña actualizada. Ya puedes iniciar sesión.")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Ir a iniciar sesión" })).toHaveAttribute("href", "/login");
  });

  it("shows the backend message when the link is not valid", async () => {
    vi.mocked(resetPassword).mockRejectedValue(apiError(400, "El enlace no es válido o ya venció."));
    const user = openLink("#token=usado");

    await fill(user, "OtraClave9");

    expect(await screen.findByRole("alert")).toHaveTextContent("El enlace no es válido o ya venció.");
  });

  it("refuses a confirmation that differs", async () => {
    const user = openLink("#token=abc");

    await fill(user, "OtraClave9", "OtraClave8");

    expect(await screen.findByText("Las contraseñas no coinciden.")).toBeInTheDocument();
    expect(resetPassword).not.toHaveBeenCalled();
  });

  it("explains a link without a token", () => {
    openLink("");

    expect(screen.getByRole("alert")).toHaveTextContent(MISSING_TOKEN);
    expect(screen.queryByLabelText("Contraseña nueva")).not.toBeInTheDocument();
  });
});
