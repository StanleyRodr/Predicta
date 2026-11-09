import { http } from "./http";
import type { SalesHistoryResponse } from "../types/etl";

/** One page of sales, newest first; ``producto`` narrows ``categoria``. */
export async function getSalesHistory(skip = 0, limit = 10, categoria?: string, producto?: string): Promise<SalesHistoryResponse> {
  const response = await http.get<SalesHistoryResponse>("/analytics/ventas", {
    params: { skip, limit, categoria: categoria || undefined, producto: (categoria && producto) || undefined },
  });
  return response.data;
}
