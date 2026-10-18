import axios from "axios";
import { afterEach, describe, expect, it, vi } from "vitest";
import { http } from "./http";
import { useAuthStore } from "../stores/authStore";

afterEach(() => {
  vi.restoreAllMocks();
  useAuthStore.getState().clearSession();
});

describe("HTTP client", () => {
  it("uses the configured backend URL", () => {
    expect(http.defaults.baseURL).toBe("http://localhost:8000");
    expect(http.defaults.timeout).toBe(15_000);
  });

  it("adds the bearer token to protected requests", async () => {
    useAuthStore.getState().setSession("session-token", null);
    let authorization: unknown;
    http.defaults.adapter = async (config) => {
      authorization = config.headers.Authorization;
      return { data: {}, status: 200, statusText: "OK", headers: {}, config };
    };

    await http.get("/users/me");

    expect(authorization).toBe("Bearer session-token");
  });

  it("clears the session after a 401 response", async () => {
    useAuthStore.getState().setSession("expired-token", null);
    http.defaults.adapter = async (config) => {
      throw new axios.AxiosError("Unauthorized", "ERR_BAD_REQUEST", config, undefined, {
        status: 401,
        statusText: "Unauthorized",
        headers: {},
        config,
        data: { detail: "No autorizado" },
      });
    };

    await expect(http.get("/users/me")).rejects.toThrow("Unauthorized");
    expect(useAuthStore.getState().token).toBeNull();
  });
});
