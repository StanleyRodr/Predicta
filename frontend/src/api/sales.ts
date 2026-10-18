import { http } from "./http";
import type { SalesHistoryResponse } from "../types/etl";

export async function getSalesHistory(skip = 0, limit = 10): Promise<SalesHistoryResponse> {
  const response = await http.get<SalesHistoryResponse>("/analytics/ventas", {
    params: { skip, limit },
  });
  return response.data;
}
