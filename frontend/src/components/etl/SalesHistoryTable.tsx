import { formatCurrency } from "../../lib/formatters";
import type { SalesHistoryResponse } from "../../types/etl";
import { Button, EmptyState, Spinner } from "../ui";

interface SalesHistoryTableProps {
  data?: SalesHistoryResponse;
  isLoading: boolean;
  page: number;
  onPageChange: (page: number) => void;
}

export function SalesHistoryTable({ data, isLoading, page, onPageChange }: SalesHistoryTableProps) {
  if (isLoading) return <Spinner label="Cargando historial" />;
  if (!data || data.registros.length === 0) {
    return <EmptyState description="Carga ventas para ver movimientos." title="Historial vacio" />;
  }

  return (
    <div className="grid gap-4">
      <div className="overflow-x-auto rounded-lg border border-terminal-border">
        <table className="w-full min-w-[42rem] text-left text-sm">
          <caption className="border-b border-terminal-border px-4 py-3 text-left font-semibold">Historial de ventas</caption>
          <thead className="bg-terminal-bg text-terminal-muted">
            <tr>
              <th className="px-4 py-3 font-medium">Fecha</th>
              <th className="px-4 py-3 font-medium">Producto</th>
              <th className="px-4 py-3 font-medium">Categoria</th>
              <th className="px-4 py-3 text-right font-medium">Monto</th>
            </tr>
          </thead>
          <tbody>
            {data.registros.map((sale) => (
              <tr className="border-t border-terminal-border" key={sale.id}>
                <td className="whitespace-nowrap px-4 py-3 font-mono text-xs text-terminal-muted">{sale.fecha}</td>
                <td className="px-4 py-3">{sale.producto}</td>
                <td className="px-4 py-3 text-terminal-muted">{sale.categoria ?? "General"}</td>
                <td className="px-4 py-3 text-right font-mono text-terminal-amber">{formatCurrency(sale.monto)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="flex items-center justify-between gap-4">
        <span className="text-sm text-terminal-muted">
          Pagina <span className="font-mono text-terminal-text">{data.pagina_actual}</span> de {data.total_paginas}
        </span>
        <div className="flex gap-2">
          <Button disabled={page === 1} onClick={() => onPageChange(page - 1)} variant="secondary">
            Anterior
          </Button>
          <Button disabled={page >= data.total_paginas} onClick={() => onPageChange(page + 1)} variant="secondary">
            Siguiente
          </Button>
        </div>
      </div>
    </div>
  );
}
