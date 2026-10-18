import axios from "axios";
import { describe, expect, it } from "vitest";
import { getApiErrorMessage } from "./apiErrors";

describe("API error messages", () => {
  it("explains backend connection failures", () => {
    const error = new axios.AxiosError("Network Error", "ERR_NETWORK");

    expect(getApiErrorMessage(error, "fallback")).toContain("iniciada en http://localhost:8000");
  });
});
