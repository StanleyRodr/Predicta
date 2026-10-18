import { describe, expect, it } from "vitest";
import { http } from "./http";

describe("HTTP client", () => {
  it("uses the configured backend URL", () => {
    expect(http.defaults.baseURL).toBe("http://localhost:8000");
    expect(http.defaults.timeout).toBe(15_000);
  });
});
