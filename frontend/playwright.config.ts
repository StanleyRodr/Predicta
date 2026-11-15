// End-to-end suite: the real API (uvicorn + PostgreSQL, seeded with the thesis
// dataset by backend/scripts/e2e_server.py) and the production build of the SPA.
import { defineConfig, devices } from "@playwright/test";
import { AUTH_STATE } from "./e2e/paths";

const API_PORT = process.env.E2E_API_PORT ?? "8001";
const WEB_PORT = "4173";
const API_URL = `http://127.0.0.1:${API_PORT}`;
const WEB_URL = `http://127.0.0.1:${WEB_PORT}`;
const PYTHON = process.env.E2E_PYTHON ?? (process.platform === "win32" ? "venv\\Scripts\\python.exe" : "python");

export default defineConfig({
  testDir: "e2e",
  outputDir: "test-results",
  // One worker: the specs share the seeded user and the API's per-IP rate limits.
  workers: 1,
  fullyParallel: false,
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? [["list"], ["html", { open: "never" }]] : "list",
  use: {
    baseURL: WEB_URL,
    // Locally the installed Chrome; in CI the Chromium that `playwright install` downloads.
    channel: process.env.CI ? undefined : "chrome",
    trace: "retain-on-failure",
  },
  projects: [
    { name: "setup", testMatch: /auth\.setup\.ts/ },
    {
      name: "chrome",
      testMatch: /.*\.spec\.ts/,
      dependencies: ["setup"],
      use: { ...devices["Desktop Chrome"], channel: process.env.CI ? undefined : "chrome", storageState: AUTH_STATE },
    },
  ],
  webServer: [
    {
      command: `${PYTHON} scripts/e2e_server.py`,
      cwd: "../backend",
      url: `${API_URL}/health`,
      env: { E2E_API_PORT: API_PORT, E2E_WEB_ORIGINS: `${WEB_URL},http://localhost:${WEB_PORT}` },
      reuseExistingServer: false,
      timeout: 180_000,
      stdout: "ignore",
    },
    {
      command: `npm run build && npx vite preview --host 127.0.0.1 --port ${WEB_PORT} --strictPort`,
      url: WEB_URL,
      env: { VITE_API_URL: API_URL },
      reuseExistingServer: false,
      timeout: 180_000,
    },
  ],
});
