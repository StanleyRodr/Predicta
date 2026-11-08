import { describe, expect, it } from "vitest";
import {
  formatAxisCurrency,
  formatCurrency,
  formatDate,
  formatDecimal,
  formatNumber,
  formatPercent,
} from "./formatters";

describe("number formatters", () => {
  it.each([
    [0, "$0.00"],
    [1234.5, "$1,234.50"],
    [1234567.891, "$1,234,567.89"],
    [-1234.5, "-$1,234.50"],
    [-0.001, "$0.00"],
  ])("formats %d as currency", (value, expected) => {
    expect(formatCurrency(value)).toBe(expected);
  });

  it("omits decimals on chart axes", () => {
    expect(formatAxisCurrency(12000)).toBe("$12,000");
    expect(formatAxisCurrency(-12000)).toBe("-$12,000");
  });

  it("formats plain numbers, fixed decimals, and percentages", () => {
    expect(formatNumber(1234567)).toBe("1,234,567");
    expect(formatNumber(1234.5)).toBe("1,234.5");
    expect(formatDecimal(1234.5)).toBe("1,234.50");
    expect(formatPercent(12.5)).toBe("12.50%");
  });
});

describe("formatDate", () => {
  it("keeps the day-first date format", () => {
    expect(formatDate("2026-01-15")).toBe("15/01/2026");
  });
});
