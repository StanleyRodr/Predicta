import { cn } from "../../lib/cn";
import { MONTH_NAMES } from "../../lib/seriesTransforms";
import type { Measure } from "../../types/analytics";
import { MEASURE_LABELS } from "./seriesChart";

export type DashboardView = "general" | "categoria" | "mes" | "historial";

export const VIEW_LABELS: Record<DashboardView, string> = {
  general: "General",
  categoria: "Por categoría",
  mes: "Por mes",
  historial: "Historial completo",
};

export interface SeriesSelection {
  view: DashboardView;
  measure: Measure;
  /** Undefined means every category. */
  categoria?: string;
  year?: number;
  month?: number;
}

interface SeriesViewSelectorProps {
  value: SeriesSelection;
  /** Receives only what the user changed, never values the view filled in by default. */
  onChange: (patch: Partial<SeriesSelection>) => void;
  categories: string[];
  years: number[];
}

const selectClass = "rounded-md border border-terminal-border bg-terminal-bg px-2 py-1.5 text-terminal-text";

function Segmented<T extends string>({
  label,
  options,
  value,
  onChange,
}: {
  label: string;
  options: Record<T, string>;
  value: T;
  onChange: (value: T) => void;
}) {
  return (
    <div aria-label={label} className="flex flex-wrap gap-1 rounded-lg border border-terminal-border p-1" role="radiogroup">
      {(Object.keys(options) as T[]).map((key) => (
        <button
          aria-checked={value === key}
          className={cn(
            "rounded-md px-3 py-1.5 text-sm transition-colors",
            value === key ? "bg-terminal-amber font-medium text-terminal-bg" : "text-terminal-muted hover:text-terminal-text",
          )}
          key={key}
          onClick={() => onChange(key)}
          role="radio"
          type="button"
        >
          {options[key]}
        </button>
      ))}
    </div>
  );
}

/** One row of controls above the charts: view, measure, category, and month. */
export function SeriesViewSelector({ value, onChange, categories, years }: SeriesViewSelectorProps) {
  return (
    <div className="grid gap-3">
      <Segmented label="Vista" onChange={(view) => onChange({ view })} options={VIEW_LABELS} value={value.view} />
      <div className="flex flex-wrap items-center gap-3">
        <Segmented label="Medida" onChange={(measure) => onChange({ measure })} options={MEASURE_LABELS} value={value.measure} />
        <label className="flex items-center gap-2 text-sm text-terminal-muted">
          Categoría
          <select
            className={selectClass}
            onChange={(event) => onChange({ categoria: event.target.value || undefined })}
            value={value.categoria ?? ""}
          >
            {value.view !== "categoria" && <option value="">Todas</option>}
            {categories.map((category) => (
              <option key={category} value={category}>
                {category}
              </option>
            ))}
          </select>
        </label>
        {value.view === "mes" && (
          <>
            <label className="flex items-center gap-2 text-sm text-terminal-muted">
              Año
              <select className={selectClass} onChange={(event) => onChange({ year: Number(event.target.value) })} value={value.year ?? ""}>
                {years.map((year) => (
                  <option key={year} value={year}>
                    {year}
                  </option>
                ))}
              </select>
            </label>
            <label className="flex items-center gap-2 text-sm text-terminal-muted">
              Mes
              <select className={selectClass} onChange={(event) => onChange({ month: Number(event.target.value) })} value={value.month ?? ""}>
                {MONTH_NAMES.map((name, index) => (
                  <option key={name} value={index + 1}>
                    {name}
                  </option>
                ))}
              </select>
            </label>
          </>
        )}
      </div>
    </div>
  );
}
