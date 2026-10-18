export interface ForecastMetrics {
  r2: number | null;
  mape: number | null;
  rmse: number | null;
}

export interface PredictionInterval {
  inferior: number;
  superior: number;
}

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

export interface ForecastUnavailable {
  error: string;
}

export type ForecastResult = ForecastResponse | ForecastUnavailable;

export function isForecastAvailable(result: ForecastResult): result is ForecastResponse {
  return !('error' in result);
}
