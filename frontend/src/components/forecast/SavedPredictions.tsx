import { formatCurrency, formatDate } from "../../lib/formatters";
import type { SavedBatch } from "../../types/forecast";
import { EmptyState } from "../ui";
import { ConceptHint } from "./ConceptHint";
import { ForecastTable, type ForecastRow } from "./ForecastTable";

const MODEL_LABELS: Record<string, string> = {
  tendencia: "Tendencia",
  tendencia_estacional: "Tendencia y temporada",
};

const savedAt = new Intl.DateTimeFormat("es-CO", { dateStyle: "medium", timeStyle: "short" });

export function savedRows(batch: SavedBatch): ForecastRow[] {
  return batch.puntos.map((point) => ({
    periodo: point.fecha_proyeccion.slice(0, 7),
    etiqueta: batch.tipo === "diaria" ? formatDate(point.fecha_proyeccion) : undefined,
    monto: point.monto_proyectado,
    cantidad: point.cantidad_proyectada,
    inferior: point.monto_inferior,
    superior: point.monto_superior,
    extrapolacion: point.extrapolacion,
  }));
}

function batchTitle(batch: SavedBatch): string {
  if (batch.tipo === "diaria") return "Proyección diaria (anterior)";
  if (batch.categoria && batch.producto) return `${batch.categoria} · ${batch.producto}`;
  return batch.categoria ? `Categoría: ${batch.categoria}` : "Todas las categorías";
}

function total(batch: SavedBatch): number | null {
  const amounts = batch.puntos.map((point) => point.monto_proyectado);
  return amounts.some((amount) => amount === null) ? null : amounts.reduce<number>((sum, amount) => sum + (amount ?? 0), 0);
}

interface SavedPredictionsProps {
  batches: SavedBatch[];
}

/** Saved projections, newest first; each one opens to its monthly table. */
export function SavedPredictions({ batches }: SavedPredictionsProps) {
  if (!batches.length) {
    return <EmptyState description="Usa “Guardar proyección” para conservar la que estás viendo." title="Aún no guardas proyecciones" />;
  }
  return (
    <div className="grid gap-3">
      <p className="flex flex-wrap items-center gap-x-1.5 text-sm text-terminal-muted">
        Cada proyección muestra su rango del 95 % <ConceptHint concept="intervalo" /> y marca los meses en extrapolación{" "}
        <ConceptHint concept="extrapolacion" />.
      </p>
      <ul className="grid gap-3">
      {batches.map((batch) => {
        const sum = total(batch);
        return (
          <li key={batch.lote}>
            <details className="rounded-lg border border-terminal-border p-4">
              <summary className="flex cursor-pointer flex-wrap items-baseline justify-between gap-2">
                <span className="font-medium">{batchTitle(batch)}</span>
                <span className="text-sm text-terminal-muted">
                  {savedAt.format(new Date(batch.fecha_creacion))}
                  {batch.modelo && ` · ${MODEL_LABELS[batch.modelo] ?? batch.modelo}`}
                  {` · ${batch.puntos.length} ${batch.puntos.length === 1 ? "mes" : "meses"}`}
                  {batch.tipo === "diaria" && " · un día"}
                  {sum !== null && ` · total ${formatCurrency(sum)}`}
                </span>
              </summary>
              <div className="mt-3">
                <ForecastTable caption={`Meses de ${batchTitle(batch)}`} hints={false} measure="monto" rows={savedRows(batch)} />
              </div>
            </details>
          </li>
        );
      })}
      </ul>
    </div>
  );
}
