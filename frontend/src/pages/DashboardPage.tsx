import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { getCategoryStats, getGlobalStats, getTemporalStats } from "../api/analytics";
import { CategoryBarChart, DateRangeFilter, MetricCard, TemporalLineChart } from "../components/analytics";
import { Alert, Card, Spinner } from "../components/ui";
import { getApiErrorMessage } from "../lib/apiErrors";
import { formatDate } from "../lib/formatters";
import { useAuthStore } from "../stores/authStore";
import type { DateRange } from "../types/analytics";

export function DashboardPage() {
  const userId = useAuthStore((state) => state.user?.id_usuario ?? null);
  const [range, setRange] = useState<DateRange>({});
  const queryKey = ["analytics", userId, range.fecha_desde ?? null, range.fecha_hasta ?? null];
  const global = useQuery({ queryKey: [...queryKey, "global"], queryFn: () => getGlobalStats(range), enabled: userId !== null });
  const categories = useQuery({ queryKey: [...queryKey, "categories"], queryFn: () => getCategoryStats(range), enabled: userId !== null });
  const temporal = useQuery({ queryKey: [...queryKey, "temporal"], queryFn: () => getTemporalStats(range), enabled: userId !== null });
  const firstError = global.error ?? categories.error ?? temporal.error;
  const metrics = global.data?.metricas_globales;

  return (
    <div className="grid gap-8">
      <header className="grid gap-2">
        <p className="font-mono text-sm text-terminal-amber">dashboard // resumen</p>
        <h1 className="text-3xl font-semibold">Tu operacion en una mirada</h1>
        <p className="text-terminal-muted">Mide lo que paso. Encuentra el siguiente movimiento.</p>
      </header>

      <DateRangeFilter onApply={setRange} onClear={() => setRange({})} value={range} />
      {(range.fecha_desde || range.fecha_hasta) && (
        <p className="text-sm text-terminal-muted">
          Rango activo: {range.fecha_desde ? formatDate(range.fecha_desde) : "inicio"} - {range.fecha_hasta ? formatDate(range.fecha_hasta) : "hoy"}
        </p>
      )}
      {firstError && <Alert tone="error">{getApiErrorMessage(firstError, "No se pudieron cargar las metricas.")}</Alert>}

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <MetricCard currency label="Ingresos totales" loading={global.isLoading} value={metrics?.total_ingresos} />
        <MetricCard label="Operaciones" loading={global.isLoading} value={metrics?.cantidad_operaciones} />
        <MetricCard currency label="Ticket promedio" loading={global.isLoading} value={metrics?.ticket_promedio} />
        <MetricCard currency label="Venta mas alta" loading={global.isLoading} value={metrics?.venta_mas_alta} />
      </div>

      <Card>
        <div className="mb-5 flex items-center justify-between gap-4">
          <div>
            <h2 className="text-lg font-semibold">Evolucion diaria</h2>
            <p className="text-sm text-terminal-muted">Ingresos observados por fecha.</p>
          </div>
          {temporal.isFetching && <Spinner label="Actualizando" />}
        </div>
        <TemporalLineChart data={temporal.data?.evolucion_diaria ?? []} />
      </Card>

      <Card>
        <div className="mb-5">
          <h2 className="text-lg font-semibold">Ingresos por categoria</h2>
          <p className="text-sm text-terminal-muted">Comparacion del rango seleccionado.</p>
        </div>
        <CategoryBarChart data={categories.data?.analisis_por_categoria ?? []} />
      </Card>
    </div>
  );
}
