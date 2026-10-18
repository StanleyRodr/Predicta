import type { PredictionInterval } from "../../types/forecast";
import { formatCurrency } from "../../lib/formatters";
import { Card } from "../ui";

interface ForecastMetricCardProps {
  label: string;
  value: number;
  interval: PredictionInterval;
  quantity?: boolean;
}

export function ForecastMetricCard({ label, value, interval, quantity = false }: ForecastMetricCardProps) {
  const format = (amount: number) => quantity ? amount.toLocaleString("es-CO", { maximumFractionDigits: 2 }) : formatCurrency(amount);
  return (
    <Card className="grid gap-4">
      <span className="text-sm text-terminal-muted">{label}</span>
      <strong className="font-mono text-3xl tabular-nums text-terminal-amber">{format(value)}</strong>
      <div className="grid gap-1 border-t border-terminal-border pt-3 text-sm text-terminal-muted">
        <span>Rango operativo</span>
        <span className="font-mono text-terminal-text">{format(interval.inferior)} - {format(interval.superior)}</span>
      </div>
    </Card>
  );
}
