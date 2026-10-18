import { http } from "./http";
import type { UploadResult } from "../types/etl";

export async function uploadSales(file: File): Promise<UploadResult> {
  const formData = new FormData();
  formData.append("file", file);
  const response = await http.post<UploadResult>("/etl/upload-ventas", formData);
  return response.data;
}

export async function clearSalesHistory(): Promise<{ status: string; message: string }> {
  const response = await http.delete<{ status: string; message: string }>("/etl/clear-history");
  return response.data;
}
