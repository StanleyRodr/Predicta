import { afterEach, describe, expect, it, vi } from "vitest";
import { analyzeColumns, clearSalesHistory, uploadSales } from "./etl";
import { getSalesHistory } from "./sales";
import { http } from "./http";

afterEach(() => vi.restoreAllMocks());

describe("sales API", () => {
  it("sends the file in the backend multipart field", async () => {
    vi.spyOn(http, "post").mockResolvedValue({ data: { errores: [] } } as never);
    const file = new File(["producto,monto,fecha"], "ventas.csv", { type: "text/csv" });

    await uploadSales(file);

    const [, body, config] = vi.mocked(http.post).mock.calls[0];
    expect(body).toBeInstanceOf(FormData);
    expect((body as FormData).get("file")).toBe(file);
    expect(config).toEqual({ timeout: 120_000 });
  });

  it("sends the mapping as JSON next to the file", async () => {
    vi.spyOn(http, "post").mockResolvedValue({ data: { errores: [] } } as never);
    const file = new File(["item,total,fecha"], "ventas.csv", { type: "text/csv" });

    await uploadSales(file, { producto: "item", monto: "total", fecha: "fecha" });

    const [, body] = vi.mocked(http.post).mock.calls[0];
    expect(JSON.parse((body as FormData).get("mapeo") as string)).toEqual({ producto: "item", monto: "total", fecha: "fecha" });
  });

  it("omits the mapping field when none is given", async () => {
    vi.spyOn(http, "post").mockResolvedValue({ data: { errores: [] } } as never);

    await uploadSales(new File(["x"], "ventas.csv"));

    const [, body] = vi.mocked(http.post).mock.calls[0];
    expect((body as FormData).has("mapeo")).toBe(false);
  });

  it("posts the file to the column analysis route", async () => {
    const post = vi.spyOn(http, "post").mockResolvedValue({ data: { columnas: [] } } as never);
    const file = new File(["x"], "ventas.xlsx");

    await analyzeColumns(file);

    const [url, body, config] = post.mock.calls[0];
    expect(url).toBe("/etl/analizar-columnas");
    expect((body as FormData).get("file")).toBe(file);
    expect(config).toEqual({ timeout: 120_000 });
  });

  it("uses pagination params and exposes clear history route", async () => {
    const get = vi.spyOn(http, "get").mockResolvedValue({ data: {} } as never);
    const remove = vi.spyOn(http, "delete").mockResolvedValue({ data: { status: "success" } } as never);

    await getSalesHistory(20, 10);
    await clearSalesHistory();

    expect(get).toHaveBeenCalledWith("/analytics/ventas", { params: { skip: 20, limit: 10 } });
    expect(remove).toHaveBeenCalledWith("/etl/clear-history");
  });
});
