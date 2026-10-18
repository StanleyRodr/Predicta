import axios from "axios";

interface ErrorBody {
  detail?: string;
}

export function getApiErrorMessage(error: unknown, fallback: string): string {
  if (!axios.isAxiosError<ErrorBody>(error)) return fallback;
  if (!error.response) {
    return "No se puede conectar con el backend. Verifica que la API este iniciada en http://localhost:8000.";
  }
  const detail = error.response?.data?.detail;
  return typeof detail === "string" ? detail : fallback;
}
