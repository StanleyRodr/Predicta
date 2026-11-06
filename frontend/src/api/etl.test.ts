import { afterEach, describe, expect, it, vi } from "vitest";
import { clearSalesHistory, uploadSales } from "./etl";
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

  it("uses pagination params and exposes clear history route", async () => {
    const get = vi.spyOn(http, "get").mockResolvedValue({ data: {} } as never);
    const remove = vi.spyOn(http, "delete").mockResolvedValue({ data: { status: "success" } } as never);

    await getSalesHistory(20, 10);
    await clearSalesHistory();

    expect(get).toHaveBeenCalledWith("/analytics/ventas", { params: { skip: 20, limit: 10 } });
    expect(remove).toHaveBeenCalledWith("/etl/clear-history");
  });
});
