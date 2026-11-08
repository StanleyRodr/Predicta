import { periodLabel } from "../../lib/seriesTransforms";
import type { ProjectedMonth } from "../../types/forecast";
import { Alert, Card } from "../ui";
import { ConceptHint } from "./ConceptHint";
import { formatForecastValue } from "./ForecastChart";
import { FORECAST_MEASURES, type ForecastMeasure } from "./forecastChartData";

interface MonthDetailProps {
  month: ProjectedMonth;
}

/** Amount and units of one projected month, each with its 95 % range. */
export function MonthDetail({ month }: MonthDetailProps) {
  return (
    <Card aria-label={`Detalle de ${periodLabel(month.periodo)}`} className="grid gap-4" role="region">
      <h2 className="font-semibold">Detalle de {periodLabel(month.periodo)}</h2>
      <div className="grid gap-4 sm:grid-cols-2">
        {(Object.keys(FORECAST_MEASURES) as ForecastMeasure[]).map((measure) => (
          <div className="grid gap-1" key={measure}>
            <span className="text-sm text-terminal-muted">{FORECAST_MEASURES[measure]} proyectado</span>
            <strong className="font-mono text-2xl tabular-nums text-terminal-amber">
              {formatForecastValue(measure, month[measure].prediccion)}
            </strong>
            <span className="flex flex-wrap items-center gap-x-1.5 font-mono text-sm text-terminal-muted">
              Entre {formatForecastValue(measure, month[measure].inferior)} y {formatForecastValue(measure, month[measure].superior)} (95 %)
              <ConceptHint concept="intervalo" />
            </span>
          </div>
        ))}
      </div>
      {month.extrapolacion && (
        <Alert className="flex flex-wrap items-center gap-x-1.5" tone="info">
          Este mes está más allá de lo que se pudo validar con tu historial: es una extrapolación{" "}
          <ConceptHint concept="extrapolacion" /> y su incertidumbre es mayor.
        </Alert>
      )}
    </Card>
  );
}
