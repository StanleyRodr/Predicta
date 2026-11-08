import { describe, expect, it } from "vitest";
import type { ValidationMetrics } from "../types/forecast";
import {
  averageEvaluatedMonth,
  explainMetric,
  metricGrade,
  overallGrade,
  qualityLabel,
  qualitySummary,
  technicalRows,
} from "./metricExplanations";

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

describe("metricGrade", () => {
  it.each([
    [0.6, "Muy buena"],
    [0.5999, "Buena"],
    [0.3, "Buena"],
    [0.2999, "Aceptable"],
    [0, "Aceptable"],
    [-0.01, "Baja"],
    [null, null],
  ])("grades an R² of %s as %s", (r2, label) => {
    expect(metricGrade("r2", metrics({ r2 }), 10_000)).toBe(label);
  });

  it.each([
    [20, "Muy buena"],
    [19.99, "Buena"],
    [5, "Buena"],
    [4.99, "Aceptable"],
    [-5, "Aceptable"],
    [-5.01, "Baja"],
    [null, null],
  ])("grades an improvement of %s as %s", (mejora_vs_referencia, label) => {
    expect(metricGrade("mejora", metrics({ mejora_vs_referencia }), 10_000)).toBe(label);
  });

  it.each([
    [999, "Muy buena"],
    [1000, "Buena"],
    [1999, "Buena"],
    [2000, "Aceptable"],
    [5000, "Aceptable"],
    [5001, "Baja"],
  ])("grades a margin of %s against a $10,000 month as %s", (rmse, label) => {
    expect(metricGrade("rmse", metrics({ rmse }), 10_000)).toBe(label);
  });

  it("cannot grade the margin without a month to compare with", () => {
    expect(metricGrade("rmse", metrics(), null)).toBeNull();
    expect(metricGrade("rmse", metrics(), 0)).toBeNull();
    expect(metricGrade("rmse", metrics({ rmse: null }), 10_000)).toBeNull();
  });

  it("grades the average error with its own ranges", () => {
    expect(metricGrade("mape", metrics({ mape: 10 }), null)).toBe("Buena");
  });
});

describe("averageEvaluatedMonth", () => {
  const history = [
    { periodo: "2025-01", monto: 900, cantidad: 9 },
    { periodo: "2025-02", monto: 100, cantidad: 1 },
    { periodo: "2025-03", monto: 300, cantidad: 3 },
  ];

  it("averages only the evaluated months, the last ones", () => {
    expect(averageEvaluatedMonth(history, "monto", 2)).toBe(200);
    expect(averageEvaluatedMonth(history, "cantidad", 3)).toBeCloseTo(13 / 3);
  });

  it("has no average without evaluated months", () => {
    expect(averageEvaluatedMonth(history, "monto", 0)).toBeNull();
    expect(averageEvaluatedMonth([], "monto", 3)).toBeNull();
  });
});

describe("overallGrade", () => {
  it("averages the available labels and rounds down", () => {
    // Buena, Buena, Muy buena, Buena: 3.25 -> Buena.
    expect(overallGrade(metrics(), 10_000)).toEqual({ label: "Buena", indicators: 4 });
    // Muy buena (4) and Aceptable (2): 3 -> Buena.
    expect(overallGrade(metrics({ mape: 5, rmse: null, r2: 0.1, mejora_vs_referencia: null }), null)).toEqual({ label: "Buena", indicators: 2 });
    // Muy buena (4) and Baja (1): 2.5 -> Aceptable, never rounded up.
    expect(overallGrade(metrics({ mape: 5, rmse: null, r2: -1, mejora_vs_referencia: null }), null)).toEqual({ label: "Aceptable", indicators: 2 });
  });

  it("has no label when nothing could be graded", () => {
    expect(overallGrade(empty, null)).toBeNull();
  });
});

describe("qualitySummary", () => {
  it("sums up the quality in one sentence", () => {
    expect(qualitySummary(metrics(), "monto", 10_000)).toBe(
      "Calidad buena según 4 indicadores, medida en los últimos 6 meses evaluados. En promedio, el monto se desvió un 12.50% del valor real.",
    );
    expect(qualitySummary(metrics({ mape: 4, rmse: null, r2: null, mejora_vs_referencia: null, origenes: 1 }), "cantidad", null)).toBe(
      "Calidad muy buena según 1 indicador, medida en el último mes evaluado. En promedio, la cantidad se desvió un 4.00% del valor real.",
    );
  });

  it("leaves out the average error when it is missing", () => {
    expect(qualitySummary(metrics({ mape: null }), "monto", 10_000)).toBe(
      "Calidad buena según 3 indicadores, medida en los últimos 6 meses evaluados.",
    );
  });

  it("explains each metric with its ranges", () => {
    for (const key of ["mape", "rmse", "r2", "mejora"] as const) {
      expect(explainMetric(key, metrics(), "monto").explanation).toMatch(/[Mm]uy buena.*buena.*aceptable.*baja/);
    }
  });

  it("does not grade a measure without any metric", () => {
    expect(qualitySummary(empty, "monto", null)).toBe(
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
