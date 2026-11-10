import axios from "axios";
import type { ColumnAnalysis, UploadResult } from "../types/etl";

/** Most files one selection may hold. */
export const MAX_BATCH_FILES = 50;
export const TOO_MANY_FILES = `Puedes cargar hasta ${MAX_BATCH_FILES} archivos a la vez.`;

export type BatchStatus = "Pendiente" | "Cargado" | "Ya cargado" | "Error" | "No válido" | "Error al analizar";

/** Natural order by name, so "x_2010Q2" comes before "x_2010Q10". */
export function sortFiles(files: File[]): File[] {
  return [...files].sort((a, b) => a.name.localeCompare(b.name, "es", { numeric: true, sensitivity: "base" }));
}

/** Files share a mapping only when their headers are the same, in the same order. */
export function headerKey(analysis: ColumnAnalysis): string {
  return JSON.stringify(analysis.columnas);
}

export interface HeaderGroup<T> {
  key: string;
  items: T[];
}

/** Group items by their headers, keeping the order in which each group first appears. */
export function groupByHeaders<T extends { analysis: ColumnAnalysis }>(items: T[]): HeaderGroup<T>[] {
  const groups = new Map<string, T[]>();
  for (const item of items) {
    const key = headerKey(item.analysis);
    groups.set(key, [...(groups.get(key) ?? []), item]);
  }
  return [...groups].map(([key, grouped]) => ({ key, items: grouped }));
}

export interface BatchTotals {
  leidos: number;
  cargados: number;
  rechazados: number;
}

/** Row totals of the files that were loaded. */
export function batchTotals(results: (UploadResult | undefined)[]): BatchTotals {
  return results.reduce<BatchTotals>(
    (totals, result) =>
      result
        ? {
            leidos: totals.leidos + result.registros_leidos,
            cargados: totals.cargados + result.registros_cargados,
            rechazados: totals.rechazados + result.filas_rechazadas,
          }
        : totals,
    { leidos: 0, cargados: 0, rechazados: 0 },
  );
}

/** Status of a file whose upload failed: a 409 means it was already loaded. */
export function fileStatus(error: unknown): "Ya cargado" | "Error" {
  return axios.isAxiosError(error) && error.response?.status === 409 ? "Ya cargado" : "Error";
}
