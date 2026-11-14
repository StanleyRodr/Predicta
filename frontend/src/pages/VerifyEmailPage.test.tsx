import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";
import { confirmEmail } from "../api/auth";
import { apiError } from "../test/apiError";
import { MISSING_TOKEN, VerifyEmailPage } from "./VerifyEmailPage";

vi.mock("../api/auth", () => ({ confirmEmail: vi.fn() }));

function openLink(hash: string) {
  window.history.replaceState(null, "", `/verificar-correo${hash}`);
  return render(
    <MemoryRouter>
      <VerifyEmailPage />
    </MemoryRouter>,
  );
}

afterEach(() => {
  vi.clearAllMocks();
  window.history.replaceState(null, "", "/");
});

describe("VerifyEmailPage", () => {
  it("sends the token from the fragment once and shows the success", async () => {
    vi.mocked(confirmEmail).mockResolvedValue({ message: "Correo confirmado. Ya puedes iniciar sesión." });

    openLink("#token=abc_123-XYZ");

    expect(await screen.findByText("Correo confirmado. Ya puedes iniciar sesión.")).toBeInTheDocument();
    expect(confirmEmail).toHaveBeenCalledTimes(1);
    expect(confirmEmail).toHaveBeenCalledWith("abc_123-XYZ");
    expect(screen.getByRole("link", { name: "Ir a iniciar sesión" })).toHaveAttribute("href", "/login");
  });

  it("removes the token from the address bar", async () => {
    vi.mocked(confirmEmail).mockResolvedValue({ message: "ok" });

    openLink("#token=secreto");

    await screen.findByText("ok");
    expect(window.location.hash).toBe("");
    expect(window.location.pathname).toBe("/verificar-correo");
  });

  it("shows the backend message when the link is not valid", async () => {
    vi.mocked(confirmEmail).mockRejectedValue(apiError(400, "El enlace no es válido o ya venció."));

    openLink("#token=usado");

    expect(await screen.findByRole("alert")).toHaveTextContent("El enlace no es válido o ya venció.");
  });

  it("explains a link without a token and calls nothing", () => {
    openLink("");

    expect(screen.getByRole("alert")).toHaveTextContent(MISSING_TOKEN);
    expect(confirmEmail).not.toHaveBeenCalled();
  });
});
