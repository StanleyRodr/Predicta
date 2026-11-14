import { act, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { changePassword } from "../../api/auth";
import { useAuthStore } from "../../stores/authStore";
import { apiError } from "../../test/apiError";
import type { User } from "../../types/api";
import { PasswordChangeCard } from "./PasswordChangeCard";

vi.mock("../../api/auth", () => ({ changePassword: vi.fn() }));

const ANA = { id_usuario: 1, nombre_usuario: "ana" } as User;

beforeEach(() => act(() => useAuthStore.getState().setSession("token-viejo", ANA)));

afterEach(() => {
  act(() => useAuthStore.getState().clearSession());
  vi.clearAllMocks();
});

async function submit(actual: string, nueva: string, confirmacion = nueva) {
  const user = userEvent.setup();
  render(<PasswordChangeCard />);
  await user.type(screen.getByLabelText("Contraseña actual"), actual);
  await user.type(screen.getByLabelText("Contraseña nueva"), nueva);
  await user.type(screen.getByLabelText("Repite la contraseña nueva"), confirmacion);
  await user.click(screen.getByRole("button", { name: "Cambiar contraseña" }));
}

describe("PasswordChangeCard", () => {
  it("keeps the session with the new token", async () => {
    vi.mocked(changePassword).mockResolvedValue({ access_token: "token-nuevo", token_type: "bearer" });

    await submit("StrongPass1", "OtraClave9");

    expect(changePassword).toHaveBeenCalledWith("StrongPass1", "OtraClave9");
    expect(await screen.findByText(/Contraseña actualizada/)).toBeInTheDocument();
    expect(useAuthStore.getState().token).toBe("token-nuevo");
    expect(useAuthStore.getState().user).toEqual(ANA);
    expect(screen.getByLabelText("Contraseña actual")).toHaveValue("");
  });

  it("shows the backend error and keeps the old token", async () => {
    vi.mocked(changePassword).mockRejectedValue(apiError(400, "La contraseña actual no es correcta."));

    await submit("Equivocada1", "OtraClave9");

    expect(await screen.findByRole("alert")).toHaveTextContent("La contraseña actual no es correcta.");
    expect(useAuthStore.getState().token).toBe("token-viejo");
  });

  it("checks the confirmation and the rules before calling the API", async () => {
    await submit("StrongPass1", "OtraClave9", "OtraClave8");
    expect(await screen.findByText("Las contraseñas no coinciden.")).toBeInTheDocument();

    expect(changePassword).not.toHaveBeenCalled();
  });

  it("refuses the same password as the current one", async () => {
    await submit("StrongPass1", "StrongPass1");

    expect(await screen.findByText("La contraseña nueva debe ser distinta de la actual.")).toBeInTheDocument();
    expect(changePassword).not.toHaveBeenCalled();
  });
});
