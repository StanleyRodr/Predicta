// REQ-50 (line chart with history and projection from the API) and REQ-53 on
// the predictions page.
import { canvasIsPainted, expect, hasHorizontalScroll, test } from "./fixtures";
import { CAPTURES } from "./paths";

const CHART = /historial y proyección de 12 meses/;

test("REQ-50: la gráfica de líneas dibuja el historial y la proyección que devuelve la API", async ({ page }) => {
  await page.goto("/predictions");
  const forecast = page.waitForResponse((response) => new URL(response.url()).pathname === "/analytics/forecast");
  await page.getByRole("button", { name: "Calcular proyección" }).click();
  const response = await forecast;
  expect(response.status()).toBe(200);
  const body = await response.json();
  expect(body.historial).toHaveLength(24);
  expect(body.proyeccion).toHaveLength(12);

  expect(await canvasIsPainted(page, CHART)).toBe(true);
  const rows = page.getByRole("table", { name: CHART }).locator("tbody tr");
  await expect(rows).toHaveCount(body.historial.length + body.proyeccion.length);
});

for (const width of [375, 1440]) {
  test(`REQ-53: las predicciones no tienen scroll horizontal a ${width} px`, async ({ page }) => {
    await page.setViewportSize({ width, height: 900 });
    await page.goto("/predictions");
    await page.getByRole("button", { name: "Calcular proyección" }).click();
    expect(await canvasIsPainted(page, CHART)).toBe(true);

    expect(await hasHorizontalScroll(page)).toBe(false);
    await page.screenshot({ path: `${CAPTURES}/predicciones-${width}.png`, fullPage: true });
  });
}
