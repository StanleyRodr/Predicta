import axios from "axios";

interface ErrorBody {
  detail?: string;
}

export function getApiErrorMessage(error: unknown, fallback: string): string {
  if (!axios.isAxiosError<ErrorBody>(error)) return fallback;
  const detail = error.response?.data?.detail;
  return typeof detail === "string" ? detail : fallback;
}
