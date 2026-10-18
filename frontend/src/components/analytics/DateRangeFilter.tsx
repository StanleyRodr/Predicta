import { useState, type FormEvent } from "react";
import { Alert, Button, Input } from "../ui";
import type { DateRange } from "../../types/analytics";

interface DateRangeFilterProps {
  value: DateRange;
  onApply: (range: DateRange) => void;
  onClear: () => void;
}

export function DateRangeFilter({ value, onApply, onClear }: DateRangeFilterProps) {
  const [draft, setDraft] = useState(value);
  const [error, setError] = useState<string | null>(null);

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (draft.fecha_desde && draft.fecha_hasta && draft.fecha_desde > draft.fecha_hasta) {
      setError("La fecha inicial no puede ser posterior a la fecha final.");
      return;
    }
    setError(null);
    onApply({
      fecha_desde: draft.fecha_desde || undefined,
      fecha_hasta: draft.fecha_hasta || undefined,
    });
  }

  function clear() {
    setDraft({});
    setError(null);
    onClear();
  }

  return (
    <form className="grid gap-3 rounded-lg border border-terminal-border bg-terminal-surface p-4" onSubmit={submit}>
      <div className="flex flex-wrap items-end gap-3">
        <Input
          aria-label="Fecha desde"
          label="Desde"
          onChange={(event) => setDraft((current) => ({ ...current, fecha_desde: event.target.value }))}
          type="date"
          value={draft.fecha_desde ?? ""}
        />
        <Input
          aria-label="Fecha hasta"
          label="Hasta"
          onChange={(event) => setDraft((current) => ({ ...current, fecha_hasta: event.target.value }))}
          type="date"
          value={draft.fecha_hasta ?? ""}
        />
        <Button type="submit">Aplicar filtro</Button>
        <Button onClick={clear} type="button" variant="ghost">Limpiar</Button>
      </div>
      {error && <Alert tone="error">{error}</Alert>}
    </form>
  );
}
