// Logs in once as the seeded user (backend/scripts/e2e_server.py) and saves the
// session, so the specs do not hit the 5-per-minute login limit.
import { expect, test as setup } from "@playwright/test";
import { AUTH_STATE } from "./paths";

const EMAIL = process.env.E2E_EMAIL ?? "e2e@example.com";
const PASSWORD = process.env.E2E_PASSWORD ?? "E2ePass1234";

setup("inicia sesión con el usuario sembrado", async ({ page }) => {
  await page.goto("/login");
  await page.getByLabel("Correo electronico").fill(EMAIL);
  await page.getByLabel("Contraseña").fill(PASSWORD);
  await page.getByRole("button", { name: "Entrar" }).click();
  await expect(page).toHaveURL(/\/dashboard$/);
  await page.context().storageState({ path: AUTH_STATE });
});
