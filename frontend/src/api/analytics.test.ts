import { afterEach, describe, expect, it, vi } from "vitest";
import { getCategoryStats, getGlobalStats, getTemporalStats } from "./analytics";
import { http } from "./http";

afterEach(() => vi.restoreAllMocks());

describe("analytics API", () => {
  it("passes the same inclusive date range to each endpoint", async () => {
    const get = vi.spyOn(http, "get").mockResolvedValue({ data: {} } as never);
    const range = { fecha_desde: "2026-01-01", fecha_hasta: "2026-01-31" };

    await getGlobalStats(range);
    await getCategoryStats(range);
    await getTemporalStats(range);

    const expected = { params: range };
    expect(get).toHaveBeenNthCalledWith(1, "/analytics/stats", expected);
    expect(get).toHaveBeenNthCalledWith(2, "/analytics/stats/categories", expected);
    expect(get).toHaveBeenNthCalledWith(3, "/analytics/stats/temporal", expected);
  });

  it("omits empty dates instead of sending invalid query values", async () => {
    const get = vi.spyOn(http, "get").mockResolvedValue({ data: {} } as never);

    await getGlobalStats({});

    expect(get).toHaveBeenCalledWith("/analytics/stats", {
      params: { fecha_desde: undefined, fecha_hasta: undefined },
    });
  });
});
