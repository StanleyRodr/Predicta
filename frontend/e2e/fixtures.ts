// Shared fixtures: every spec fails if the page logs a console error or throws
// (REQ-62: charts render without synchronization errors).
import { expect, test as base, type Page } from "@playwright/test";

export const test = base.extend<{ consoleErrors: string[] }>({
  consoleErrors: [
    async ({ page }, use) => {
      const errors: string[] = [];
      page.on("console", (message) => {
        if (message.type() === "error") errors.push(message.text());
      });
      page.on("pageerror", (error) => errors.push(error.message));
      // The console only says "Failed to load resource"; keep the URL that failed.
      page.on("response", (response) => {
        if (response.status() >= 400) errors.push(`${response.status()} ${response.url()}`);
      });
      await use(errors);
      expect(errors, "errores en la consola del navegador").toEqual([]);
    },
    { auto: true },
  ],
});

export { expect };

/** True when a chart canvas has painted pixels, compared with a blank canvas of the same size. */
export async function canvasIsPainted(page: Page, chartName: string | RegExp): Promise<boolean> {
  const chart = page.getByRole("img", { name: chartName });
  await expect(chart).toBeVisible();
  const canvas = chart.locator("canvas").first();
  await expect(canvas).toBeVisible();
  // Chart.js animates the first draw; give it a moment before reading pixels.
  await page.waitForTimeout(800);
  return canvas.evaluate((element: HTMLCanvasElement) => {
    const blank = document.createElement("canvas");
    blank.width = element.width;
    blank.height = element.height;
    return element.width > 0 && element.height > 0 && element.toDataURL() !== blank.toDataURL();
  });
}

/** True when the page is wider than its viewport (REQ-53 asks for none). */
export async function hasHorizontalScroll(page: Page): Promise<boolean> {
  return page.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth);
}
