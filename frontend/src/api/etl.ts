import { http, LONG_REQUEST_TIMEOUT_MS } from "./http";
import type { UploadResult } from "../types/etl";

export async function uploadSales(file: File): Promise<UploadResult> {
  const formData = new FormData();
  formData.append("file", file);
  const response = await http.post<UploadResult>("/etl/upload-ventas", formData, { timeout: LONG_REQUEST_TIMEOUT_MS });
  return response.data;
}

export async function clearSalesHistory(): Promise<{ status: string; message: string }> {
  const response = await http.delete<{ status: string; message: string }>("/etl/clear-history");
  return response.data;
}
