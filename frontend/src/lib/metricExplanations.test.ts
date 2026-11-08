import { describe, expect, it } from "vitest";
import type { ValidationMetrics } from "../types/forecast";
import { explainMetric, qualityLabel, qualitySummary, technicalRows } from "./metricExplanations";

function metrics(overrides: Partial<ValidationMetrics> = {}): ValidationMetrics {
  return {
    r2: 0.8,
    mape: 12.5,
    rmse: 1250,
    wape: 11,
    mase: 0.6,
    mejora_vs_referencia: 18,
    referencia: "mismo_mes_anio_anterior",
    origenes: 6,
    ...overrides,
  };
}

const empty = metrics({ r2: null, mape: null, rmse: null, wape: null, mase: null, mejora_vs_referencia: null, referencia: null, origenes: 0 });

describe("explainMetric", () => {
  it("builds plain sentences with the right unit for normal values", () => {
    expect(explainMetric("mape", metrics(), "monto").sentence).toBe("Se desvía en promedio un 12.50% del valor real.");
    expect(explainMetric("rmse", metrics(), "monto").sentence).toBe("Suele fallar por unos $1,250.00.");
    expect(explainMetric("rmse", metrics({ rmse: 1250.5 }), "cantidad").sentence).toBe("Suele fallar por unos 1,250.5 unidades.");
    expect(explainMetric("r2", metrics(), "monto").sentence).toBe(
      "Explica cerca del 80% de los cambios en las ventas de los meses evaluados.",
    );
    expect(explainMetric("mejora", metrics(), "monto").sentence).toBe(
      "Se equivoca 18% menos que repetir el mismo mes del año anterior.",
    );
  });

  it("keeps the acronym as secondary data and never calls R² precision", () => {
    const r2 = explainMetric("r2", metrics(), "monto");
    expect(r2.title).toBe("Patrón explicado");
    expect(r2.acronym).toBe("R²");
    expect(`${r2.title} ${r2.sentence} ${r2.explanation}`.toLowerCase()).not.toContain("precisión");
  });

  it("describes zero values without inventing an error", () => {
    expect(explainMetric("mape", metrics({ mape: 0 }), "monto").sentence).toBe("No se desvió del valor real en los meses evaluados.");
    expect(explainMetric("rmse", metrics({ rmse: 0 }), "monto").sentence).toBe("No tuvo error en los meses evaluados.");
    expect(explainMetric("r2", metrics({ r2: 0 }), "monto").sentence).toMatch(/rinde igual que usar el promedio/);
    expect(explainMetric("mejora", metrics({ mejora_vs_referencia: 0 }), "monto").sentence).toBe(
      "Se equivoca lo mismo que repetir el mismo mes del año anterior.",
    );
  });

  it("says when the model loses for negative values", () => {
    expect(explainMetric("r2", metrics({ r2: -0.4 }), "monto").sentence).toBe("Rinde peor que usar el promedio de los meses evaluados.");
    expect(explainMetric("mejora", metrics({ mejora_vs_referencia: -25, referencia: "ultimo_valor" }), "monto").sentence).toBe(
      "Se equivoca 25% más que repetir las ventas del mes anterior.",
    );
  });

  it("shows null as unavailable with a reason, never as zero", () => {
    for (const key of ["mape", "rmse", "r2", "mejora"] as const) {
      const metric = explainMetric(key, empty, "monto");
      expect(metric.available).toBe(false);
      expect(metric.sentence).toMatch(/^No disponible\. Tu historial todavía no deja meses/);
      expect(metric.sentence).not.toMatch(/\b0(\.00)?\b|\$0/);
    }
    expect(explainMetric("r2", metrics({ r2: null, origenes: 1 }), "monto").sentence).toMatch(/al menos dos meses/);
    expect(explainMetric("r2", metrics({ r2: null }), "monto").sentence).toMatch(/no variaron/);
    expect(explainMetric("mape", metrics({ mape: null }), "monto").sentence).toMatch(/no tuvieron ventas/);
  });
});

describe("qualityLabel", () => {
  it.each([
    [0, "Muy buena"],
    [9.99, "Muy buena"],
    [10, "Buena"],
    [19.99, "Buena"],
    [20, "Aceptable"],
    [50, "Aceptable"],
    [50.01, "Baja"],
    [null, null],
  ])("labels %s as %s", (mape, label) => {
    expect(qualityLabel(mape)).toBe(label);
  });
});

describe("qualitySummary", () => {
  it("sums up the quality in one sentence", () => {
    expect(qualitySummary(metrics(), "monto")).toBe(
      "Calidad buena: en los últimos 6 meses evaluados, el monto se desvió en promedio un 12.50% del valor real.",
    );
    expect(qualitySummary(metrics({ mape: 4, origenes: 1 }), "cantidad")).toBe(
      "Calidad muy buena: en el último mes evaluado, la cantidad se desvió en promedio un 4.00% del valor real.",
    );
  });

  it("does not grade a measure without an average error", () => {
    expect(qualitySummary(empty, "monto")).toBe(
      "Aún no se puede calificar el monto. Tu historial todavía no deja meses para comprobar el modelo.",
    );
  });
});

describe("technicalRows", () => {
  it("formats every raw metric with its unit and keeps null unavailable", () => {
    expect(technicalRows(metrics(), "monto").map((row) => row.value)).toEqual(["0.80", "12.50%", "$1,250.00", "11.00%", "0.60", "6"]);
    expect(technicalRows(metrics({ rmse: 3 }), "cantidad")[2].value).toBe("3 unidades");
    expect(technicalRows(empty, "monto").map((row) => row.value)).toEqual([
      "No disponible",
      "No disponible",
      "No disponible",
      "No disponible",
      "No disponible",
      "0",
    ]);
  });
});
