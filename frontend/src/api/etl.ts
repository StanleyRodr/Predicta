import { http, LONG_REQUEST_TIMEOUT_MS } from "./http";
import type { ColumnAnalysis, ColumnMapping, UploadResult } from "../types/etl";

function fileForm(file: File): FormData {
  const formData = new FormData();
  formData.append("file", file);
  return formData;
}

export async function analyzeColumns(file: File): Promise<ColumnAnalysis> {
  const response = await http.post<ColumnAnalysis>("/etl/analizar-columnas", fileForm(file), { timeout: LONG_REQUEST_TIMEOUT_MS });
  return response.data;
}

export async function uploadSales(file: File, mapeo?: ColumnMapping): Promise<UploadResult> {
  const formData = fileForm(file);
  if (mapeo) formData.append("mapeo", JSON.stringify(mapeo));
  const response = await http.post<UploadResult>("/etl/upload-ventas", formData, { timeout: LONG_REQUEST_TIMEOUT_MS });
  return response.data;
}

export async function clearSalesHistory(): Promise<{ status: string; message: string }> {
  const response = await http.delete<{ status: string; message: string }>("/etl/clear-history");
  return response.data;
}
