import { http } from "./http";
import type {
  CategoryStatsResponse,
  DateRange,
  GlobalStatsResponse,
  ProductListResponse,
  SeriesParams,
  SeriesResponse,
  TemporalStatsResponse,
} from "../types/analytics";

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

/** Products the user sold within one category, sorted by name. */
export async function getProducts(categoria: string): Promise<ProductListResponse> {
  const response = await http.get<ProductListResponse>("/analytics/productos", { params: { categoria } });
  return response.data;
}

export async function getTemporalStats(range: DateRange): Promise<TemporalStatsResponse> {
  const response = await http.get<TemporalStatsResponse>("/analytics/stats/temporal", { params: params(range) });
  return response.data;
}

export async function getSalesSeries(params: SeriesParams): Promise<SeriesResponse> {
  const response = await http.get<SeriesResponse>("/analytics/stats/series", {
    params: {
      ...params,
      fecha_desde: params.fecha_desde || undefined,
      fecha_hasta: params.fecha_hasta || undefined,
      categoria: params.categoria || undefined,
      por_categoria: params.por_categoria || undefined,
    },
  });
  return response.data;
}
