import { http } from "./http";
import type { ForecastResponse, MonthlyForecastResponse, SavedBatch, SavedBatchPage } from "../types/forecast";

/** Next-day forecast. Never stores anything. */
export async function getForecast(): Promise<ForecastResponse> {
  const response = await http.get<ForecastResponse>("/analytics/predict");
  return response.data;
}

/** Monthly projection, overall, for one category, or for one of its products. Never stores anything. */
export async function getMonthlyForecast(categoria?: string, producto?: string): Promise<MonthlyForecastResponse> {
  const response = await http.get<MonthlyForecastResponse>("/analytics/forecast", {
    params: { categoria: categoria || undefined, producto: (categoria && producto) || undefined },
  });
  return response.data;
}

/** Saves the projection the server recomputes; no client value is sent. */
export async function savePrediction(categoria?: string, producto?: string): Promise<SavedBatch> {
  const response = await http.post<SavedBatch>("/analytics/predicciones", {
    categoria: categoria || null,
    producto: (categoria && producto) || null,
  });
  return response.data;
}

export async function listSavedPredictions(skip = 0, limit = 10): Promise<SavedBatchPage> {
  const response = await http.get<SavedBatchPage>("/analytics/predicciones", { params: { skip, limit } });
  return response.data;
}
