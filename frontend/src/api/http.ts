import axios from "axios";
import { useAuthStore } from "../stores/authStore";

// Uploads and generated reports can outlast the default timeout.
export const LONG_REQUEST_TIMEOUT_MS = 120_000;

export const http = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? "http://localhost:8000",
  timeout: 15_000,
  headers: { Accept: "application/json" },
});

http.interceptors.request.use((config) => {
  const token = useAuthStore.getState().token;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

http.interceptors.response.use(
  (response) => response,
  (error: unknown) => {
    if (axios.isAxiosError(error) && error.response?.status === 401) {
      useAuthStore.getState().clearSession();
      window.dispatchEvent(new Event("predicta:unauthorized"));
    }
    return Promise.reject(error);
  },
);
