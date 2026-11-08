import { describe, expect, it } from "vitest";
import { CONCEPTS, MODEL_NAMES } from "./conceptExplanations";

describe("concept explanations", () => {
  it("gives every concept a title and a full-sentence explanation", () => {
    for (const { title, explanation } of Object.values(CONCEPTS)) {
      expect(title.trim()).not.toBe("");
      expect(explanation).toMatch(/^[A-ZÁÉÍÓÚÑ¿].*\.$/);
    }
  });

  it("keeps the Spanish accents", () => {
    expect(CONCEPTS.extrapolacion.title).toBe("extrapolación");
    expect(CONCEPTS.cautela.explanation).toContain("proyección");
    expect(CONCEPTS.rangoDiario.title).toBe("rango del día siguiente");
  });

  it("does not promise certainty about the interval", () => {
    expect(CONCEPTS.intervalo.explanation).toContain("unos 95");
    expect(CONCEPTS.intervalo.explanation).not.toMatch(/siempre|seguro que/i);
  });

  it("names both models", () => {
    expect(MODEL_NAMES).toEqual({ tendencia: "solo tendencia", tendencia_estacional: "tendencia y temporada" });
  });
});
