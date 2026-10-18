import type { ForecastMetrics } from "../../types/forecast";
import { Card } from "../ui";

interface ForecastQualityProps {
  amount: ForecastMetrics;
  quantity: ForecastMetrics;
}

function Metric({ label, value }: { label: string; value: number | null }) {
  return (
    <div className="grid gap-1">
      <span className="text-xs text-terminal-muted">{label}</span>
      <strong className="font-mono text-lg">{value === null ? "No disponible" : value.toFixed(2)}</strong>
    </div>
  );
}

export function ForecastQuality({ amount, quantity }: ForecastQualityProps) {
  return (
    <Card className="grid gap-5">
      <div className="grid gap-1">
        <h2 className="font-semibold">Calidad del modelo</h2>
        <p className="text-sm leading-6 text-terminal-muted">Metricas calculadas con validacion temporal. Un historial corto puede dejar valores no disponibles.</p>
      </div>
      <div className="grid gap-5 sm:grid-cols-2">
        <div className="grid gap-3">
          <span className="text-sm text-terminal-amber">Monto</span>
          <div className="grid grid-cols-3 gap-3"><Metric label="R²" value={amount.r2} /><Metric label="MAPE" value={amount.mape} /><Metric label="RMSE" value={amount.rmse} /></div>
        </div>
        <div className="grid gap-3">
          <span className="text-sm text-terminal-amber">Cantidad</span>
          <div className="grid grid-cols-3 gap-3"><Metric label="R²" value={quantity.r2} /><Metric label="MAPE" value={quantity.mape} /><Metric label="RMSE" value={quantity.rmse} /></div>
        </div>
      </div>
    </Card>
  );
}
