// Mirrors the backend schemas in backend/app/schemas/schemas.py.

export interface ForecastMetrics {
  r2: number | null;
  mape: number | null;
  rmse: number | null;
}

export interface PredictionInterval {
  inferior: number;
  superior: number;
}

/** GET /analytics/predict. Too little history answers 422 with a Spanish `detail`. */
export interface ForecastResponse {
  usuario: string;
  proxima_fecha: string;
  monto_predicho: number;
  cantidad_predicha: number;
  monto_original_crudo: number;
  intervalos_prediccion: {
    monto: PredictionInterval;
    cantidad: PredictionInterval;
  };
  metricas: {
    monto: ForecastMetrics;
    cantidad: ForecastMetrics;
  };
  mensaje: string;
}

export type MonthlyModel = "tendencia" | "tendencia_estacional";

export type BaselineName = "ultimo_valor" | "mismo_mes_anio_anterior" | "promedio_movil_3";

export interface MonthTotals {
  /** YYYY-MM */
  periodo: string;
  monto: number;
  cantidad: number;
}

export interface ProjectedValue {
  prediccion: number;
  /** Bounds of the 95 % prediction interval. */
  inferior: number;
  superior: number;
}

export interface ProjectedMonth {
  periodo: string;
  /** True from month 7: unvalidated extrapolation. */
  extrapolacion: boolean;
  monto: ProjectedValue;
  cantidad: ProjectedValue;
}

/** Errors on months the model did not see; null when they cannot be computed. */
export interface ValidationMetrics {
  r2: number | null;
  mape: number | null;
  rmse: number | null;
  wape: number | null;
  mase: number | null;
  mejora_vs_referencia: number | null;
  referencia: BaselineName | null;
  origenes: number;
}

/** GET /analytics/forecast. It never stores anything. */
export interface MonthlyForecastResponse {
  usuario: string;
  /** null: every category. */
  categoria: string | null;
  modelo: MonthlyModel;
  horizonte_aplicado: number;
  meses_observados: number;
  /** Every reason that limits the projection, one sentence each. */
  advertencias: string[];
  /** The same reasons joined in one text. */
  advertencia: string | null;
  historial: MonthTotals[];
  /** The last, still incomplete month: projected, not fitted. */
  mes_parcial: MonthTotals | null;
  proyeccion: ProjectedMonth[];
  metricas: {
    monto: ValidationMetrics;
    cantidad: ValidationMetrics;
  };
}

export interface SavedPoint {
  fecha_proyeccion: string;
  extrapolacion: boolean | null;
  monto_proyectado: number | null;
  monto_inferior: number | null;
  monto_superior: number | null;
  cantidad_proyectada: number;
  cantidad_inferior: number | null;
  cantidad_superior: number | null;
}

/** POST /analytics/predicciones and each entry of GET /analytics/predicciones. */
export interface SavedBatch {
  lote: string;
  tipo: "mensual" | "diaria";
  categoria: string | null;
  modelo: string | null;
  horizonte: number | null;
  r2_validacion: number | null;
  wape_validacion: number | null;
  fecha_creacion: string;
  puntos: SavedPoint[];
}

export interface SavedBatchPage {
  usuario: string;
  total_lotes: number;
  pagina_actual: number;
  total_paginas: number;
  lotes: SavedBatch[];
}
