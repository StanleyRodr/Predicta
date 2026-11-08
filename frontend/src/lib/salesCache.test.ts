import { QueryClient } from "@tanstack/react-query";
import { describe, expect, it } from "vitest";
import { refreshSalesData } from "./salesCache";

describe("refreshSalesData", () => {
  it("invalidates sales data and drops stale forecasts", async () => {
    const queryClient = new QueryClient();
    queryClient.setQueryData(["analytics", 1, null, null, "global"], { total: 1 });
    queryClient.setQueryData(["sales-history", 1, 1], { registros: [] });
    queryClient.setQueryData(["forecast", 1], { monto_predicho: 1 });

    await refreshSalesData(queryClient);

    expect(queryClient.getQueryState(["analytics", 1, null, null, "global"])?.isInvalidated).toBe(true);
    expect(queryClient.getQueryState(["sales-history", 1, 1])?.isInvalidated).toBe(true);
    expect(queryClient.getQueryData(["forecast", 1])).toBeUndefined();
  });
});
