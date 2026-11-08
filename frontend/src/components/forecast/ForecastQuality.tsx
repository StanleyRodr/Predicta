import { useId, useState } from "react";
import {
  averageEvaluatedMonth,
  explainMetric,
  METRIC_KEYS,
  metricGrade,
  overallGrade,
  qualitySummary,
  technicalRows,
  type MetricMeasure,
  type QualityLabel,
} from "../../lib/metricExplanations";
import type { MonthTotals, ValidationMetrics } from "../../types/forecast";
import { Badge, Card, InfoHint } from "../ui";

interface ForecastQualityProps {
  amount: ValidationMetrics;
  quantity: ValidationMetrics;
  /** Complete months; the evaluated ones give the scale of the typical margin. */
  history: MonthTotals[];
}

const LABEL_TONES: Record<QualityLabel, "positive" | "neutral" | "warning" | "error"> = {
  "Muy buena": "positive",
  Buena: "positive",
  Aceptable: "warning",
  Baja: "error",
};

const MEASURE_TITLES: Record<MetricMeasure, string> = { monto: "Monto", cantidad: "Cantidad" };

function GradeBadge({ grade, label }: { grade: QualityLabel | null; label: string }) {
  // The hidden prefix tells screen readers which metric the label belongs to.
  return (
    <Badge data-testid="grade" tone={grade ? LABEL_TONES[grade] : "neutral"}>
      <span className="sr-only">{label}: </span>
      {grade ?? "Sin dato"}
    </Badge>
  );
}

function MeasureQuality({ measure, metrics, history }: { measure: MetricMeasure; metrics: ValidationMetrics; history: MonthTotals[] }) {
  const averageMonth = averageEvaluatedMonth(history, measure, metrics.origenes);
  const overall = overallGrade(metrics, averageMonth);
  return (
    <section aria-label={`Calidad de ${MEASURE_TITLES[measure].toLowerCase()}`} className="grid content-start gap-4">
      <div className="flex flex-wrap items-center gap-2">
        <h3 className="text-sm text-terminal-amber">{MEASURE_TITLES[measure]}</h3>
        {overall && (
          <Badge data-testid="overall-grade" tone={LABEL_TONES[overall.label]}>
            <span className="sr-only">Calidad general: </span>
            {overall.label}
          </Badge>
        )}
      </div>
      <p className="text-sm leading-6">{qualitySummary(metrics, measure, averageMonth)}</p>
      <dl className="grid gap-4">
        {METRIC_KEYS.map((key) => {
          const metric = explainMetric(key, metrics, measure);
          return (
            <div className="grid gap-1" key={key}>
              <dt className="flex flex-wrap items-center gap-2 text-sm font-medium">
                {metric.title}
                <InfoHint label={metric.title.toLowerCase()}>{metric.explanation}</InfoHint>
                <span className="font-mono text-xs font-normal text-terminal-muted">{metric.acronym}</span>
                <GradeBadge grade={metricGrade(key, metrics, averageMonth)} label={metric.title} />
              </dt>
              <dd className={metric.available ? "text-sm leading-6" : "text-sm leading-6 text-terminal-muted"}>{metric.sentence}</dd>
            </div>
          );
        })}
      </dl>
    </section>
  );
}

function TechnicalDetail({ amount, quantity }: Omit<ForecastQualityProps, "history">) {
  const [open, setOpen] = useState(false);
  const panelId = useId();
  const amountRows = technicalRows(amount, "monto");
  const quantityRows = technicalRows(quantity, "cantidad");

  return (
    <div className="grid gap-3 border-t border-terminal-border pt-4">
      <button
        aria-controls={panelId}
        aria-expanded={open}
        className="justify-self-start text-sm text-terminal-muted hover:text-terminal-text"
        onClick={() => setOpen((value) => !value)}
        type="button"
      >
        <span aria-hidden="true">{open ? "▾" : "▸"}</span> Detalle técnico
      </button>
      <div hidden={!open} id={panelId}>
        <table className="w-full text-left text-sm">
          <caption className="sr-only">Métricas técnicas de la validación</caption>
          <thead className="text-terminal-muted">
            <tr>
              <th scope="col">Métrica</th>
              <th scope="col">Monto</th>
              <th scope="col">Cantidad</th>
            </tr>
          </thead>
          <tbody className="font-mono tabular-nums">
            {amountRows.map((row, index) => (
              <tr key={row.acronym}>
                <th className="font-sans font-normal text-terminal-muted" scope="row">
                  {row.acronym}
                </th>
                <td>{row.value}</td>
                <td>{quantityRows[index].value}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export function ForecastQuality({ amount, quantity, history }: ForecastQualityProps) {
  return (
    <Card aria-label="Qué tan confiable es la proyección" className="grid gap-5">
      <div className="grid gap-1">
        <h2 className="font-semibold">¿Qué tan confiable es?</h2>
        <p className="text-sm leading-6 text-terminal-muted">
          Medido prediciendo meses pasados que el modelo no vio. Las etiquetas son orientativas: cada indicador tiene la suya, con
          sus rangos en su botón «i», y la de Monto o Cantidad es el promedio de todas.
        </p>
      </div>
      <div className="grid gap-6 sm:grid-cols-2">
        <MeasureQuality history={history} measure="monto" metrics={amount} />
        <MeasureQuality history={history} measure="cantidad" metrics={quantity} />
      </div>
      <TechnicalDetail amount={amount} quantity={quantity} />
    </Card>
  );
}
