export interface DateRange {
  fecha_desde?: string;
  fecha_hasta?: string;
}

export interface GlobalMetrics {
  total_ingresos: number;
  cantidad_operaciones: number;
  ticket_promedio: number;
  venta_mas_alta: number;
}

export interface GlobalStatsResponse {
  usuario: string;
  metricas_globales: GlobalMetrics;
}

export interface CategoryMetric {
  categoria: string;
  ingresos_totales: number;
  cantidad_ventas: number;
  ticket_promedio: number;
}

export interface CategoryStatsResponse {
  usuario: string;
  analisis_por_categoria: CategoryMetric[];
}

export interface TemporalMetric {
  fecha: string;
  ingresos: number;
  ventas_realizadas: number;
}

export interface TemporalStatsResponse {
  usuario: string;
  evolucion_diaria: TemporalMetric[];
}
