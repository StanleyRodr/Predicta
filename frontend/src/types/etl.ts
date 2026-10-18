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
