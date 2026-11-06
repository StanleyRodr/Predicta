import { Card, Spinner } from "../ui";
import { formatCurrency, formatNumber } from "../../lib/formatters";

interface MetricCardProps {
  label: string;
  value: number | undefined;
  currency?: boolean;
  loading?: boolean;
}

export function MetricCard({ label, value, currency = false, loading = false }: MetricCardProps) {
  return (
    <Card className="grid gap-3">
      <span className="text-sm text-terminal-muted">{label}</span>
      {loading ? (
        <Spinner label="Cargando" />
      ) : (
        <strong className="font-mono text-2xl tabular-nums text-terminal-text">
          {value === undefined ? "--" : currency ? formatCurrency(value) : formatNumber(value)}
        </strong>
      )}
    </Card>
  );
}
