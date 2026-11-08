import axios from "axios";
import { getApiErrorMessage } from "../lib/apiErrors";
import { http, LONG_REQUEST_TIMEOUT_MS } from "./http";

const DOWNLOAD_ERROR = "No se pudo descargar el reporte.";
// Some browsers cancel the download if the URL is revoked right after click().
const REVOKE_DELAY_MS = 10_000;

function filenameFromHeader(header: string | undefined, fallback: string): string {
  const match = header?.match(/filename\*?=(?:UTF-8''|")?([^;"]+)/i);
  if (!match?.[1]) return fallback;
  try {
    return decodeURIComponent(match[1].trim().replace(/^"|"$/g, ""));
  } catch {
    return fallback;
  }
}

export async function downloadReport(path: string, fallback: string): Promise<void> {
  const response = await http.get<Blob>(path, { responseType: "blob", timeout: LONG_REQUEST_TIMEOUT_MS });
  const filename = filenameFromHeader(response.headers["content-disposition"], fallback);
  const url = URL.createObjectURL(response.data);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), REVOKE_DELAY_MS);
}

export async function reportErrorMessage(error: unknown): Promise<string> {
  // With responseType "blob", error bodies also arrive as a Blob.
  const body: unknown = axios.isAxiosError(error) ? error.response?.data : undefined;
  if (!(body instanceof Blob)) return getApiErrorMessage(error, DOWNLOAD_ERROR);
  try {
    const parsed = JSON.parse(await body.text()) as { detail?: unknown };
    return typeof parsed.detail === "string" ? parsed.detail : DOWNLOAD_ERROR;
  } catch {
    return DOWNLOAD_ERROR;
  }
}
