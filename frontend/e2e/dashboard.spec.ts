// REQ-51 (bars by category), REQ-53 (responsive) and REQ-54 (updates without a
// full page load) on the dashboard, with the thesis dataset served by the API.
import { canvasIsPainted, expect, hasHorizontalScroll, test } from "./fixtures";
import { CAPTURES } from "./paths";

const CATEGORIES = ["Abarrotes", "Bebidas", "Cuidado Personal", "Limpieza", "Lácteos"];

test("REQ-51: la gráfica de barras muestra los ingresos de las 5 categorías", async ({ page }) => {
  await page.goto("/dashboard");
  await page.getByRole("radio", { name: "Por categoría" }).click();

  expect(await canvasIsPainted(page, "Ingresos por categoría")).toBe(true);
  const rows = page.getByRole("table", { name: "Datos de Ingresos por categoría" }).locator("tbody tr th");
  await expect(rows).toHaveCount(CATEGORIES.length);
  expect((await rows.allTextContents()).sort()).toEqual(CATEGORIES);
});

test("REQ-54: cambiar la vista y el filtro de fechas no recarga la página", async ({ page }) => {
  await page.goto("/dashboard");
  await expect(page.getByRole("img", { name: /un año por línea/ })).toBeVisible();
  let loads = 0;
  page.on("load", () => {
    loads += 1;
  });

  await page.getByRole("radio", { name: "Por categoría" }).click();
  await expect(page.getByRole("img", { name: "Ingresos por categoría" })).toBeVisible();
  const filtered = page.waitForResponse(
    (response) => response.url().includes("/analytics/stats?") && response.url().includes("fecha_desde=2026-01-01"),
  );
  await page.getByLabel("Fecha desde").fill("2026-01-01");
  await page.getByRole("button", { name: "Aplicar filtro" }).click();
  expect((await filtered).status()).toBe(200);
  await expect(page.getByText(/Rango activo:/)).toContainText("2026");

  expect(loads).toBe(0);
});

for (const width of [375, 1440]) {
  test(`REQ-53: el dashboard no tiene scroll horizontal a ${width} px`, async ({ page }) => {
    await page.setViewportSize({ width, height: 900 });
    await page.goto("/dashboard");
    expect(await canvasIsPainted(page, /un año por línea/)).toBe(true);

    expect(await hasHorizontalScroll(page)).toBe(false);
    await page.screenshot({ path: `${CAPTURES}/dashboard-${width}.png`, fullPage: true });
  });
}
