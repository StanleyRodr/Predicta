import { act, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { updateCurrentUser } from "../api/auth";
import { useAuthStore } from "../stores/authStore";
import { apiError } from "../test/apiError";
import type { User } from "../types/api";
import { ProfilePage } from "./ProfilePage";

vi.mock("../api/auth", () => ({ updateCurrentUser: vi.fn() }));

const ANA: User = {
  id_usuario: 1,
  nombre_usuario: "ana",
  correo_electronico: "ana@example.com",
  id_rol: 2,
  fecha_registro: "2026-01-01T00:00:00Z",
  correo_verificado: true,
  correo_pendiente: null,
};

function setUser(user: User) {
  act(() => useAuthStore.setState({ user }));
}

beforeEach(() => setUser(ANA));

afterEach(() => {
  act(() => useAuthStore.getState().clearSession());
  vi.clearAllMocks();
});

async function changeEmail(email: string) {
  const user = userEvent.setup();
  render(<ProfilePage />);
  const field = screen.getByLabelText("Correo electronico");
  await user.clear(field);
  await user.type(field, email);
  return user;
}

describe("ProfilePage", () => {
  it("asks for the current password only when the e-mail changes", async () => {
    const user = userEvent.setup();
    render(<ProfilePage />);
    expect(screen.queryByLabelText("Contraseña actual")).not.toBeInTheDocument();

    const field = screen.getByLabelText("Correo electronico");
    await user.clear(field);
    await user.type(field, "nueva@example.com");

    expect(screen.getByLabelText("Contraseña actual")).toBeInTheDocument();
  });

  it("refuses an e-mail change without the current password", async () => {
    const user = await changeEmail("nueva@example.com");
    await user.click(screen.getByRole("button", { name: "Guardar cambios" }));

    expect(await screen.findByText("Escribe tu contraseña actual para cambiar el correo.")).toBeInTheDocument();
    expect(updateCurrentUser).not.toHaveBeenCalled();
  });

  it("sends the password with the new e-mail and shows the pending notice", async () => {
    vi.mocked(updateCurrentUser).mockResolvedValue({ ...ANA, correo_pendiente: "nueva@example.com" });

    const user = await changeEmail("Nueva@Example.com");
    await user.type(screen.getByLabelText("Contraseña actual"), "StrongPass1");
    await user.click(screen.getByRole("button", { name: "Guardar cambios" }));

    expect(updateCurrentUser).toHaveBeenCalledWith({
      nombre_usuario: "ana",
      correo_electronico: "nueva@example.com",
      password_actual: "StrongPass1",
    });
    expect(await screen.findByText(/Te enviamos un enlace a nueva@example.com/)).toBeInTheDocument();
    expect(screen.getByText(/Falta confirmar nueva@example.com/)).toBeInTheDocument();
  });

  it("updates only the username without asking for the password", async () => {
    vi.mocked(updateCurrentUser).mockResolvedValue({ ...ANA, nombre_usuario: "ana_maria" });
    const user = userEvent.setup();
    render(<ProfilePage />);

    const field = screen.getByLabelText("Nombre de usuario");
    await user.clear(field);
    await user.type(field, "ana_maria");
    await user.click(screen.getByRole("button", { name: "Guardar cambios" }));

    expect(updateCurrentUser).toHaveBeenCalledWith({ nombre_usuario: "ana_maria" });
    expect(await screen.findByText("Perfil actualizado.")).toBeInTheDocument();
  });

  it("shows the backend error for a wrong current password", async () => {
    vi.mocked(updateCurrentUser).mockRejectedValue(apiError(400, "La contraseña actual no es correcta."));

    const user = await changeEmail("nueva@example.com");
    await user.type(screen.getByLabelText("Contraseña actual"), "Otra12345");
    await user.click(screen.getByRole("button", { name: "Guardar cambios" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("La contraseña actual no es correcta.");
  });
});
