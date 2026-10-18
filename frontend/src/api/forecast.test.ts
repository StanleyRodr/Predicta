import { afterEach, describe, expect, it, vi } from "vitest";
import { getForecast } from "./forecast";
import { http } from "./http";

afterEach(() => vi.restoreAllMocks());

describe("forecast API", () => {
  it("requests prediction only through the explicit endpoint", async () => {
    const get = vi.spyOn(http, "get").mockResolvedValue({ data: { error: "Se necesitan mas dias" } } as never);

    const result = await getForecast();

    expect(get).toHaveBeenCalledWith("/analytics/predict");
    expect(result).toEqual({ error: "Se necesitan mas dias" });
  });
});
