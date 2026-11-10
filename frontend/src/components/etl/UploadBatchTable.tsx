import { useState } from "react";
import { formatNumber } from "../../lib/formatters";
import { batchTotals, type BatchStatus } from "../../lib/uploadBatch";
import type { UploadResult } from "../../types/etl";
import { Badge, Button } from "../ui";
import { UploadSummary } from "./UploadSummary";

export interface BatchRow {
  name: string;
  status: BatchStatus;
  result?: UploadResult;
  message?: string;
}

const STATUS_TONES: Record<BatchStatus, "neutral" | "positive" | "warning" | "error"> = {
  Pendiente: "neutral",
  Cargado: "positive",
  "Ya cargado": "warning",
  Error: "error",
  "No válido": "error",
  "Error al analizar": "error",
};

interface UploadBatchTableProps {
  rows: BatchRow[];
}

/** One row per selected file with its status, row counts and, on demand, its summary. */
export function UploadBatchTable({ rows }: UploadBatchTableProps) {
  const [detail, setDetail] = useState<number | null>(null);
  const loaded = rows.filter((row) => row.result);
  const totals = batchTotals(rows.map((row) => row.result));
  const detailRow = detail === null ? undefined : rows[detail];

  return (
    <div className="grid gap-4">
      <div className="overflow-x-auto rounded-lg border border-terminal-border">
        <table className="w-full min-w-[40rem] text-left text-sm">
          <caption className="border-b border-terminal-border px-4 py-3 text-left font-semibold">Archivos seleccionados</caption>
          <thead className="bg-terminal-bg text-terminal-muted">
            <tr>
              <th className="px-4 py-3 font-medium" scope="col">Archivo</th>
              <th className="px-4 py-3 font-medium" scope="col">Estado</th>
              <th className="px-4 py-3 text-right font-medium" scope="col">Leidos</th>
              <th className="px-4 py-3 text-right font-medium" scope="col">Cargados</th>
              <th className="px-4 py-3 text-right font-medium" scope="col">Rechazados</th>
              <th className="px-4 py-3 font-medium" scope="col">Detalle</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row, index) => (
              <tr className="border-t border-terminal-border" key={`${index}-${row.name}`}>
                <th className="px-4 py-3 font-mono text-xs font-normal" scope="row">{row.name}</th>
                <td className="px-4 py-3">
                  <Badge tone={STATUS_TONES[row.status]}>{row.status}</Badge>
                </td>
                <td className="px-4 py-3 text-right font-mono">{row.result ? formatNumber(row.result.registros_leidos) : ""}</td>
                <td className="px-4 py-3 text-right font-mono text-terminal-positive">{row.result ? formatNumber(row.result.registros_cargados) : ""}</td>
                <td className="px-4 py-3 text-right font-mono text-terminal-error">{row.result ? formatNumber(row.result.filas_rechazadas) : ""}</td>
                <td className="px-4 py-3 text-terminal-muted">
                  {row.result ? (
                    <Button
                      aria-label={`Ver detalle de ${row.name}`}
                      aria-pressed={detail === index}
                      onClick={() => setDetail(detail === index ? null : index)}
                      variant="secondary"
                    >
                      {detail === index ? "Ocultar" : "Ver detalle"}
                    </Button>
                  ) : (
                    row.message
                  )}
                </td>
              </tr>
            ))}
          </tbody>
          {loaded.length > 0 && (
            <tfoot className="border-t border-terminal-border font-semibold">
              <tr>
                <th className="px-4 py-3" scope="row">Total</th>
                <td className="px-4 py-3 text-terminal-muted">
                  {loaded.length} de {rows.length} cargados
                </td>
                <td className="px-4 py-3 text-right font-mono">{formatNumber(totals.leidos)}</td>
                <td className="px-4 py-3 text-right font-mono text-terminal-positive">{formatNumber(totals.cargados)}</td>
                <td className="px-4 py-3 text-right font-mono text-terminal-error">{formatNumber(totals.rechazados)}</td>
                <td />
              </tr>
            </tfoot>
          )}
        </table>
      </div>
      {detailRow?.result && (
        <section aria-label={`Detalle de ${detailRow.name}`} className="grid gap-2">
          <h3 className="font-mono text-sm text-terminal-amber">{detailRow.name}</h3>
          <UploadSummary result={detailRow.result} />
        </section>
      )}
    </div>
  );
}
