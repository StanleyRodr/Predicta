import { cn } from "../../lib/cn";
import { formatCurrency, formatNumber } from "../../lib/formatters";
import { periodLabel } from "../../lib/seriesTransforms";
import { Badge } from "../ui";
import { ConceptHint } from "./ConceptHint";
import type { ForecastMeasure } from "./forecastChartData";

export interface ForecastRow {
  /** YYYY-MM */
  periodo: string;
  /** Overrides the month label, for rows that are a single day. */
  etiqueta?: string;
  monto: number | null;
  cantidad: number | null;
  inferior: number | null;
  superior: number | null;
  extrapolacion: boolean | null;
}

const MISSING = "—";

function money(value: number | null): string {
  return value === null ? MISSING : formatCurrency(value);
}

function units(value: number | null): string {
  return value === null ? MISSING : formatNumber(value);
}

interface ForecastTableProps {
  rows: ForecastRow[];
  /** The range column shows this measure's interval. */
  measure: ForecastMeasure;
  selected?: string | null;
  onSelect?: (periodo: string) => void;
  caption: string;
}

/** Projected months with amount, units, and the 95 % range; a null value is shown as missing, never as zero. */
export function ForecastTable({ rows, measure, selected = null, onSelect, caption }: ForecastTableProps) {
  const range = measure === "monto" ? money : units;
  // One explanation per table: on the first extrapolated month only.
  const firstExtrapolated = rows.find((row) => row.extrapolacion)?.periodo;
  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[32rem] text-left text-sm">
        <caption className="sr-only">{caption}</caption>
        <thead className="text-terminal-muted">
          <tr className="border-b border-terminal-border">
            <th className="py-2 pr-3 font-medium" scope="col">Mes</th>
            <th className="py-2 pr-3 text-right font-medium" scope="col">Monto</th>
            <th className="py-2 pr-3 text-right font-medium" scope="col">Cantidad</th>
            <th className="py-2 pr-3 text-right font-medium" scope="col">
              <span className="inline-flex items-center gap-1.5">
                Rango 95 % ({measure === "monto" ? "monto" : "cantidad"})
                <ConceptHint concept="intervalo" />
              </span>
            </th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => {
            const isSelected = row.periodo === selected;
            return (
              <tr
                aria-selected={onSelect ? isSelected : undefined}
                className={cn("border-b border-terminal-border/60", isSelected && "bg-terminal-amber/10")}
                key={row.periodo}
              >
                <th className="py-2 pr-3 font-normal" scope="row">
                  {onSelect ? (
                    <button className="text-left underline-offset-2 hover:underline" onClick={() => onSelect(row.periodo)} type="button">
                      {row.etiqueta ?? periodLabel(row.periodo)}
                    </button>
                  ) : (
                    (row.etiqueta ?? periodLabel(row.periodo))
                  )}
                  {row.extrapolacion && (
                    <Badge className="ml-2" tone="warning">
                      Extrapolación
                    </Badge>
                  )}
                  {row.periodo === firstExtrapolated && (
                    <span className="ml-1.5 inline-flex align-middle">
                      <ConceptHint concept="extrapolacion" />
                    </span>
                  )}
                </th>
                <td className="py-2 pr-3 text-right font-mono tabular-nums">{money(row.monto)}</td>
                <td className="py-2 pr-3 text-right font-mono tabular-nums">{units(row.cantidad)}</td>
                <td className="py-2 pr-3 text-right font-mono tabular-nums">
                  {row.inferior === null && row.superior === null ? MISSING : `${range(row.inferior)} – ${range(row.superior)}`}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
