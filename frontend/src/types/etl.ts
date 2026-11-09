export interface UploadRowError {
  fila: number;
  error: string;
}

export interface UploadResult {
  message: string;
  registros_leidos: number;
  registros_cargados: number;
  filas_rechazadas: number;
  errores: UploadRowError[];
}

export interface SaleRecord {
  id: number;
  producto: string;
  monto: number;
  categoria: string | null;
  fecha: string;
}

export interface SalesHistoryResponse {
  usuario: string;
  total_registros: number;
  pagina_actual: number;
  total_paginas: number;
  registros: SaleRecord[];
}

export type ColumnRole = "producto" | "categoria" | "monto" | "precio_unitario" | "cantidad" | "fecha";

/** Role -> file header. "Sin asignar" omits the key. */
export type ColumnMapping = Partial<Record<ColumnRole, string>>;

export interface ColumnProposal {
  columna: string | null;
  origen: "exacto" | "sinonimo" | null;
  candidatos: string[];
}

export interface ColumnAnalysis {
  columnas: string[];
  muestra: Record<string, string | null>[];
  propuesta: Record<ColumnRole, ColumnProposal>;
  faltantes: ColumnRole[];
}
