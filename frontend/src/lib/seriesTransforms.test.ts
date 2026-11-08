import { describe, expect, it } from "vitest";
import type { SeriesPoint } from "../types/analytics";
import {
  categoryLinesData,
  latestMonth,
  monthBounds,
  monthDaysData,
  monthlyTimelineData,
  periodLabel,
  yearMonthsData,
  yearOverlayData,
} from "./seriesTransforms";

function point(anio: number, mes: number, ingresos: number, extra: Partial<SeriesPoint> = {}): SeriesPoint {
  return {
    periodo: `${anio}-${String(mes).padStart(2, "0")}`,
    anio,
    mes,
    dia: null,
    categoria: null,
    ingresos,
    cantidad: ingresos / 10,
    ventas_realizadas: 1,
    ...extra,
  };
}

describe("series transforms", () => {
  it("overlays years and leaves months without sales as null, never zero", () => {
    const data = yearOverlayData([point(2025, 1, 10), point(2024, 11, 5), point(2024, 12, 7)], "ingresos");

    expect(data.labels).toHaveLength(12);
    expect(data.series.map((series) => series.key)).toEqual([2024, 2025]);
    expect(data.series[0].values.slice(0, 10)).toEqual(Array(10).fill(null));
    expect(data.series[0].values.slice(10)).toEqual([5, 7]);
    expect(data.series[1].values[0]).toBe(10);
    expect(data.series[1].values.slice(1)).toEqual(Array(11).fill(null));
  });

  it("reads the chosen measure", () => {
    expect(yearOverlayData([point(2025, 3, 40)], "cantidad").series[0].values[2]).toBe(4);
  });

  it("keeps a gap for a month between two observed ones", () => {
    const data = monthlyTimelineData([point(2025, 1, 10), point(2025, 3, 30)], "ingresos");

    expect(data.labels).toEqual(["2025-01", "2025-02", "2025-03"]);
    expect(data.series[0].values).toEqual([10, null, 30]);
  });

  it("builds one line per category on a shared timeline", () => {
    const data = categoryLinesData(
      [point(2025, 1, 10, { categoria: "Lácteos" }), point(2025, 2, 20, { categoria: "Abarrotes" })],
      "ingresos",
    );

    expect(data.labels).toEqual(["2025-01", "2025-02"]);
    expect(data.series).toEqual([
      { key: "Abarrotes", values: [null, 20] },
      { key: "Lácteos", values: [10, null] },
    ]);
  });

  it("lists the twelve months of one year", () => {
    const values = yearMonthsData([point(2024, 5, 1), point(2025, 5, 2)], 2025, "ingresos");

    expect(values[4]).toBe(2);
    expect(values.filter((value) => value !== null)).toHaveLength(1);
  });

  it("lists every day of the month with gaps for days without sales", () => {
    const data = monthDaysData([point(2024, 2, 9, { dia: 3, periodo: "2024-02-03" })], 2024, 2, "ingresos");

    expect(data.labels).toHaveLength(29);
    expect(data.series[0].values[2]).toBe(9);
    expect(data.series[0].values.filter((value) => value !== null)).toEqual([9]);
  });

  it("opens the month view on the last month with sales", () => {
    expect(latestMonth([point(2025, 12, 1), point(2026, 2, 1), point(2025, 3, 1)])).toEqual({ year: 2026, month: 2 });
    expect(latestMonth([])).toBeNull();
  });

  it("clips a month to the active date range", () => {
    expect(monthBounds(2025, 2, {})).toEqual({ fecha_desde: "2025-02-01", fecha_hasta: "2025-02-28" });
    expect(monthBounds(2025, 2, { fecha_desde: "2025-02-10", fecha_hasta: "2025-03-31" })).toEqual({
      fecha_desde: "2025-02-10",
      fecha_hasta: "2025-02-28",
    });
  });

  it("labels periods with Spanish month names", () => {
    expect(periodLabel("2025-09")).toBe("Sep 2025");
  });
});
