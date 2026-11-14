import { afterEach, describe, expect, it, vi } from "vitest";
import {
  changePassword,
  confirmEmail,
  forgotPassword,
  getCurrentUser,
  loginUser,
  registerUser,
  resendVerification,
  resetPassword,
} from "./auth";
import { http } from "./http";

afterEach(() => vi.restoreAllMocks());

describe("auth API", () => {
  it("sends login credentials as form data", async () => {
    vi.spyOn(http, "post").mockResolvedValue({
      data: { access_token: "token", token_type: "bearer" },
    } as never);

    await loginUser("ana@example.com", "Secret1");

    expect(http.post).toHaveBeenCalledWith(
      "/users/login",
      expect.any(URLSearchParams),
      expect.objectContaining({
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
      }),
    );
  });

  it("uses backend routes for registration and current user", async () => {
    const post = vi.spyOn(http, "post").mockResolvedValue({ data: { id_usuario: 1 } } as never);
    const get = vi.spyOn(http, "get").mockResolvedValue({ data: { id_usuario: 1 } } as never);

    await registerUser({ nombre_usuario: "ana", correo_electronico: "ana@example.com", password: "Secret1a" });
    await getCurrentUser();

    expect(post).toHaveBeenCalledWith("/users/register", expect.any(Object));
    expect(get).toHaveBeenCalledWith("/users/me");
  });

  it("posts the e-mail to resend and the token to confirm", async () => {
    const post = vi.spyOn(http, "post").mockResolvedValue({ data: { message: "ok" } } as never);

    await resendVerification("ana@example.com");
    await confirmEmail("abc");

    expect(post).toHaveBeenNthCalledWith(1, "/users/verificacion/reenviar", { correo_electronico: "ana@example.com" });
    expect(post).toHaveBeenNthCalledWith(2, "/users/verificacion/confirmar", { token: "abc" });
  });

  it("uses the password routes", async () => {
    const post = vi.spyOn(http, "post").mockResolvedValue({ data: { message: "ok" } } as never);
    const put = vi.spyOn(http, "put").mockResolvedValue({ data: { access_token: "t" } } as never);

    await forgotPassword("ana@example.com");
    await resetPassword("abc", "OtraClave9");
    await changePassword("StrongPass1", "OtraClave9");

    expect(post).toHaveBeenNthCalledWith(1, "/users/contrasena/olvido", { correo_electronico: "ana@example.com" });
    expect(post).toHaveBeenNthCalledWith(2, "/users/contrasena/restablecer", { token: "abc", password_nueva: "OtraClave9" });
    expect(put).toHaveBeenCalledWith("/users/me/password", { password_actual: "StrongPass1", password_nueva: "OtraClave9" });
  });
});
