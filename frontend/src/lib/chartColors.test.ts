import { describe, expect, it } from "vitest";
import { categoryColor, SERIES_COLORS, yearColor } from "./chartColors";

describe("chart colors", () => {
  it("gives each year a fixed color, whatever other years are shown", () => {
    expect(yearColor(2025)).toBe(yearColor(2025));
    expect(yearColor(2025)).not.toBe(yearColor(2026));
    expect(SERIES_COLORS).toContain(yearColor(1999));
  });

  it("keeps a category color when the list order changes", () => {
    const all = ["Lácteos", "Abarrotes", "Bebidas"];

    expect(categoryColor("Bebidas", all)).toBe(SERIES_COLORS[1]);
    expect(categoryColor("Bebidas", [...all].reverse())).toBe(SERIES_COLORS[1]);
  });
});
