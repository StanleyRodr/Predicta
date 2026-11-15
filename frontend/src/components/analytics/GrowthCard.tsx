import { Card, Spinner } from "../ui";
import { formatPercent } from "../../lib/formatters";
import type { MonthlyGrowth } from "../../types/analytics";

const MONTHS = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"];

/** "+10.00%", "-5.50%"; the sign makes the direction readable without color. */
function signed(value: number): string {
  return `${value > 0 ? "+" : ""}${formatPercent(value)}`;
}

function monthLabel(period: string): string {
  const [year, month] = period.split("-").map(Number);
  return `${MONTHS[month - 1]} ${year}`;
}

interface GrowthCardProps {
  growth: MonthlyGrowth | null | undefined;
  loading?: boolean;
}

/** Revenue change of the last complete month against the previous one and a year earlier. */
export function GrowthCard({ growth, loading = false }: GrowthCardProps) {
  const main = growth?.vs_mes_anterior ?? null;
  return (
    <Card className="grid gap-3">
      <span className="text-sm text-terminal-muted">Crecimiento mensual</span>
      {loading ? (
        <Spinner label="Cargando" />
      ) : growth === undefined ? (
        <strong className="font-mono text-2xl tabular-nums text-terminal-text">--</strong>
      ) : growth === null || main === null ? (
        <strong className="text-base text-terminal-text">Sin datos suficientes</strong>
      ) : (
        <strong className="font-mono text-2xl tabular-nums text-terminal-text">{signed(main)}</strong>
      )}
      {!loading && growth && (
        <span className="text-xs text-terminal-muted">
          {monthLabel(growth.periodo)} vs mes anterior
          {growth.vs_anio_anterior !== null && ` · ${signed(growth.vs_anio_anterior)} vs año anterior`}
        </span>
      )}
    </Card>
  );
}
