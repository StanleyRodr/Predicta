import { afterEach, describe, expect, it, vi } from "vitest";
import { getCurrentUser, loginUser, registerUser } from "./auth";
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
});
