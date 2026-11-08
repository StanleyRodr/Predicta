import axios from "axios";
import { apiBaseUrl } from "./apiUrl";

interface ErrorBody {
  detail?: string;
}

export function getApiErrorMessage(error: unknown, fallback: string): string {
  if (!axios.isAxiosError<ErrorBody>(error)) return fallback;
  if (!error.response) {
    return `No se puede conectar con el backend. Verifica que la API esté iniciada en ${apiBaseUrl()}.`;
  }
  const detail = error.response?.data?.detail;
  return typeof detail === "string" ? detail : fallback;
}
