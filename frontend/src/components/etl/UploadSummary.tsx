import type { UploadResult } from "../../types/etl";
import { Alert, Card } from "../ui";

interface UploadSummaryProps {
  result: UploadResult;
}

export function UploadSummary({ result }: UploadSummaryProps) {
  const completion = result.registros_leidos
    ? Math.round((result.registros_cargados / result.registros_leidos) * 100)
    : 0;

  return (
    <div className="grid gap-4">
      <Alert tone={result.filas_rechazadas ? "info" : "success"}>{result.message}</Alert>
      <div className="grid gap-3 sm:grid-cols-3">
        <Card>
          <span className="text-sm text-terminal-muted">Leidos</span>
          <strong className="mt-2 font-mono text-2xl">{result.registros_leidos}</strong>
        </Card>
        <Card>
          <span className="text-sm text-terminal-muted">Cargados</span>
          <strong className="mt-2 font-mono text-2xl text-terminal-positive">{result.registros_cargados}</strong>
        </Card>
        <Card>
          <span className="text-sm text-terminal-muted">Rechazados</span>
          <strong className="mt-2 font-mono text-2xl text-terminal-error">{result.filas_rechazadas}</strong>
        </Card>
      </div>
      <div className="grid gap-2">
        <div className="flex justify-between text-xs text-terminal-muted">
          <span>Procesamiento valido</span>
          <span className="font-mono">{completion}%</span>
        </div>
        <div aria-label={`${completion}% procesado`} className="h-2 rounded-full bg-terminal-border" role="progressbar" aria-valuemax={100} aria-valuemin={0} aria-valuenow={completion}>
          <div className="h-full rounded-full bg-terminal-positive" style={{ width: `${completion}%` }} />
        </div>
      </div>
      {result.errores.length > 0 && (
        <div className="overflow-x-auto rounded-lg border border-terminal-border">
          <table className="w-full min-w-96 text-left text-sm">
            <caption className="border-b border-terminal-border px-4 py-3 text-left font-semibold">Errores por fila</caption>
            <thead className="bg-terminal-bg text-terminal-muted">
              <tr>
                <th className="px-4 py-3 font-medium">Fila</th>
                <th className="px-4 py-3 font-medium">Detalle</th>
              </tr>
            </thead>
            <tbody>
              {result.errores.map((item) => (
                <tr className="border-t border-terminal-border" key={`${item.fila}-${item.error}`}>
                  <td className="px-4 py-3 font-mono">{item.fila}</td>
                  <td className="px-4 py-3 text-terminal-muted">{item.error}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
