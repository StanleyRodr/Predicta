// Plain-language explanations of the forecast concepts on /predictions. Every
// new concept shown on the page gets a title and an explanation here.
import type { MonthlyModel } from "../types/forecast";

export type ConceptKey = "intervalo" | "extrapolacion" | "cautela" | "mesParcial" | "modelo" | "rangoDiario" | "guardadas";

export interface ConceptExplanation {
  /** Name of the concept, used to label its info button. */
  title: string;
  explanation: string;
}

export const CONCEPTS: Record<ConceptKey, ConceptExplanation> = {
  intervalo: {
    title: "intervalo del 95 %",
    explanation:
      "Es el rango donde casi seguro caerá la venta real: de cada 100 meses, unos 95 quedarían dentro de la zona sombreada. Una zona ancha significa más incertidumbre.",
  },
  extrapolacion: {
    title: "extrapolación",
    explanation:
      "Meses más lejanos que los que se pudieron comprobar con tu historial. Son una estimación más arriesgada: úsalos como orientación, no como cifra segura.",
  },
  cautela: {
    title: "tomar la proyección con cautela",
    explanation:
      "La proyección sigue siendo útil, pero algo de tu historial limita su precisión. Abajo están los motivos; cargar más meses de ventas suele resolverlos.",
  },
  mesParcial: {
    title: "mes en curso",
    explanation:
      "El mes actual todavía no termina, así que no se usa para calcular la tendencia: se proyecta como si fuera futuro.",
  },
  modelo: {
    title: "tipo de modelo",
    explanation:
      "Solo tendencia: sigue la dirección general de tus ventas. Tendencia y temporada: además repite los altibajos de cada mes del año; se usa desde 36 meses con todos los meses del año.",
  },
  rangoDiario: {
    title: "rango del día siguiente",
    explanation: "Igual que en la proyección mensual: la venta de mañana probablemente caerá entre estos dos valores.",
  },
  guardadas: {
    title: "proyecciones guardadas",
    explanation:
      "Calcular una proyección no guarda nada. Al guardarla queda una copia con fecha para compararla después con lo que realmente vendiste.",
  },
};

export const MODEL_NAMES: Record<MonthlyModel, string> = {
  tendencia: "solo tendencia",
  tendencia_estacional: "tendencia y temporada",
};
