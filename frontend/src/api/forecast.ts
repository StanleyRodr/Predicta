import { http } from "./http";
import type { ForecastResult } from "../types/forecast";

export async function getForecast(): Promise<ForecastResult> {
  const response = await http.get<ForecastResult>("/analytics/predict");
  return response.data;
}
