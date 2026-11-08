import axios from "axios";
import { afterEach, describe, expect, it, vi } from "vitest";
import { getApiErrorMessage } from "./apiErrors";

describe("API error messages", () => {
  afterEach(() => {
    vi.unstubAllEnvs();
  });

  it("explains backend connection failures", () => {
    const error = new axios.AxiosError("Network Error", "ERR_NETWORK");

    expect(getApiErrorMessage(error, "fallback")).toContain("iniciada en http://localhost:8000");
  });

  it("names the configured API URL in the connection message", () => {
    vi.stubEnv("VITE_API_URL", "https://api.predicta.test");
    const error = new axios.AxiosError("Network Error", "ERR_NETWORK");

    expect(getApiErrorMessage(error, "fallback")).toBe(
      "No se puede conectar con el backend. Verifica que la API esté iniciada en https://api.predicta.test.",
    );
  });
});
