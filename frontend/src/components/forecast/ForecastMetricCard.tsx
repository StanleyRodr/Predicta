import type { PredictionInterval } from "../../types/forecast";
import { formatCurrency, formatNumber } from "../../lib/formatters";
import { Card } from "../ui";
import { ConceptHint } from "./ConceptHint";

interface ForecastMetricCardProps {
  label: string;
  value: number;
  interval: PredictionInterval;
  quantity?: boolean;
}

export function ForecastMetricCard({ label, value, interval, quantity = false }: ForecastMetricCardProps) {
  const format = quantity ? formatNumber : formatCurrency;
  return (
    <Card className="grid gap-4">
      <span className="text-sm text-terminal-muted">{label}</span>
      <strong className="font-mono text-3xl tabular-nums text-terminal-amber">{format(value)}</strong>
      <div className="grid gap-1 border-t border-terminal-border pt-3 text-sm text-terminal-muted">
        <span className="flex items-center gap-2">
          Rango probable <ConceptHint concept="rangoDiario" />
        </span>
        <span className="font-mono text-terminal-text">{format(interval.inferior)} - {format(interval.superior)}</span>
      </div>
    </Card>
  );
}
