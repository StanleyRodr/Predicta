export const DEFAULT_API_URL = "http://localhost:8000";

/** Backend base URL: `VITE_API_URL`, or the local API by default. */
export function apiBaseUrl(): string {
  return import.meta.env.VITE_API_URL || DEFAULT_API_URL;
}
