import { afterEach, describe, expect, it, vi } from "vitest";
import { getCategoryStats, getGlobalStats, getSalesSeries, getTemporalStats } from "./analytics";
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

describe("sales series API", () => {
  it("sends the series filters and drops empty ones", async () => {
    const get = vi.spyOn(http, "get").mockResolvedValue({ data: {} } as never);

    await getSalesSeries({ granularidad: "dia", categoria: "Lácteos", fecha_desde: "2026-01-01", fecha_hasta: "" });
    await getSalesSeries({ granularidad: "mes", categoria: "", por_categoria: false });

    expect(get).toHaveBeenNthCalledWith(1, "/analytics/stats/series", {
      params: {
        granularidad: "dia",
        categoria: "Lácteos",
        fecha_desde: "2026-01-01",
        fecha_hasta: undefined,
        por_categoria: undefined,
      },
    });
    expect(get).toHaveBeenNthCalledWith(2, "/analytics/stats/series", {
      params: { granularidad: "mes", categoria: undefined, por_categoria: undefined, fecha_desde: undefined, fecha_hasta: undefined },
    });
  });
});
