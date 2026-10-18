import axios from "axios";
import { http } from "./http";

function filenameFromHeader(header: string | undefined, fallback: string): string {
  const match = header?.match(/filename\*?=(?:UTF-8''|\")?([^;\"]+)/i);
  if (!match?.[1]) return fallback;
  try {
    return decodeURIComponent(match[1].trim().replace(/^"|"$/g, ""));
  } catch {
    return fallback;
  }
}

export async function downloadReport(path: string, fallback: string): Promise<void> {
  const response = await http.get<Blob>(path, { responseType: "blob" });
  const filename = filenameFromHeader(response.headers["content-disposition"], fallback);
  const url = URL.createObjectURL(response.data);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}

export function reportErrorMessage(error: unknown): string {
  if (!axios.isAxiosError(error)) return "No se pudo descargar el reporte.";
  return typeof error.response?.data?.detail === "string"
    ? error.response.data.detail
    : "No se pudo descargar el reporte.";
}
