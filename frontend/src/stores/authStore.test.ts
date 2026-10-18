import { beforeEach, describe, expect, it } from "vitest";
import { TOKEN_KEY, useAuthStore } from "./authStore";

const user = {
  id_usuario: 1,
  nombre_usuario: "ana",
  correo_electronico: "ana@example.com",
  id_rol: 2,
  fecha_registro: "2026-01-01T00:00:00Z",
};

describe("auth store", () => {
  beforeEach(() => {
    localStorage.clear();
    useAuthStore.setState({
      token: null,
      user: null,
      isHydrated: false,
      isCheckingSession: false,
    });
  });

  it("persists session and clears all auth data on logout", () => {
    useAuthStore.getState().setSession("token-value", user);
    expect(localStorage.getItem(TOKEN_KEY)).toBe("token-value");
    expect(useAuthStore.getState().user?.nombre_usuario).toBe("ana");

    useAuthStore.getState().clearSession();
    expect(localStorage.getItem(TOKEN_KEY)).toBeNull();
    expect(useAuthStore.getState().token).toBeNull();
    expect(useAuthStore.getState().user).toBeNull();
  });

  it("hydrates a stored token and marks session check as pending", () => {
    localStorage.setItem(TOKEN_KEY, "stored-token");

    useAuthStore.getState().hydrate();

    expect(useAuthStore.getState().token).toBe("stored-token");
    expect(useAuthStore.getState().isHydrated).toBe(true);
    expect(useAuthStore.getState().isCheckingSession).toBe(true);
  });
});
