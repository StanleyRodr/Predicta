import { http } from "./http";
import type { CategoryStatsResponse, DateRange, GlobalStatsResponse, TemporalStatsResponse } from "../types/analytics";

function params(range: DateRange) {
  return {
    fecha_desde: range.fecha_desde || undefined,
    fecha_hasta: range.fecha_hasta || undefined,
  };
}

export async function getGlobalStats(range: DateRange): Promise<GlobalStatsResponse> {
  const response = await http.get<GlobalStatsResponse>("/analytics/stats", { params: params(range) });
  return response.data;
}

export async function getCategoryStats(range: DateRange): Promise<CategoryStatsResponse> {
  const response = await http.get<CategoryStatsResponse>("/analytics/stats/categories", { params: params(range) });
  return response.data;
}

export async function getTemporalStats(range: DateRange): Promise<TemporalStatsResponse> {
  const response = await http.get<TemporalStatsResponse>("/analytics/stats/temporal", { params: params(range) });
  return response.data;
}
