import { afterEach, describe, expect, it, vi } from "vitest";
import { getForecast, getMonthlyForecast, listSavedPredictions, savePrediction } from "./forecast";
import { http } from "./http";

afterEach(() => vi.restoreAllMocks());

describe("forecast API", () => {
  it("requests the next-day forecast only through the explicit endpoint", async () => {
    const get = vi.spyOn(http, "get").mockResolvedValue({ data: { monto_predicho: 10 } } as never);

    const result = await getForecast();

    expect(get).toHaveBeenCalledWith("/analytics/predict");
    expect(result).toEqual({ monto_predicho: 10 });
  });

  it("asks for the monthly projection with an optional category", async () => {
    const get = vi.spyOn(http, "get").mockResolvedValue({ data: {} } as never);

    await getMonthlyForecast();
    await getMonthlyForecast("Lácteos");

    expect(get).toHaveBeenNthCalledWith(1, "/analytics/forecast", { params: { categoria: undefined } });
    expect(get).toHaveBeenNthCalledWith(2, "/analytics/forecast", { params: { categoria: "Lácteos" } });
  });

  it("saves by naming only the category, never the values", async () => {
    const post = vi.spyOn(http, "post").mockResolvedValue({ data: { lote: "abc" } } as never);

    await savePrediction();
    await savePrediction("Bebidas");
    await savePrediction("Bebidas", "Coca Cola");
    await savePrediction(undefined, "Coca Cola");

    expect(post).toHaveBeenNthCalledWith(1, "/analytics/predicciones", { categoria: null, producto: null });
    expect(post).toHaveBeenNthCalledWith(2, "/analytics/predicciones", { categoria: "Bebidas", producto: null });
    expect(post).toHaveBeenNthCalledWith(3, "/analytics/predicciones", { categoria: "Bebidas", producto: "Coca Cola" });
    // A product is never sent without its category.
    expect(post).toHaveBeenNthCalledWith(4, "/analytics/predicciones", { categoria: null, producto: null });
  });

  it("asks for a product's projection together with its category", async () => {
    const get = vi.spyOn(http, "get").mockResolvedValue({ data: {} } as never);

    await getMonthlyForecast("Bebidas", "Coca Cola");

    expect(get).toHaveBeenCalledWith("/analytics/forecast", { params: { categoria: "Bebidas", producto: "Coca Cola" } });
  });

  it("pages through saved projections", async () => {
    const get = vi.spyOn(http, "get").mockResolvedValue({ data: {} } as never);

    await listSavedPredictions(10, 5);

    expect(get).toHaveBeenCalledWith("/analytics/predicciones", { params: { skip: 10, limit: 5 } });
  });
});
