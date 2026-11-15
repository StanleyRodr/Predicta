import { useQuery } from "@tanstack/react-query";
import { useState, type ReactNode } from "react";
import { getCategoryStats, getGlobalStats, getSalesSeries } from "../api/analytics";
import {
  CategoryBarChart,
  CategoryComparisonChart,
  DateRangeFilter,
  GrowthCard,
  HistoryLineChart,
  MetricCard,
  MonthDetailChart,
  MonthTotalsChart,
  SeriesViewSelector,
  YearOverlayChart,
  type SeriesSelection,
} from "../components/analytics";
import { Alert, Card, Spinner } from "../components/ui";
import { getApiErrorMessage } from "../lib/apiErrors";
import { SERIES_COLORS } from "../lib/chartColors";
import { formatDate } from "../lib/formatters";
import { latestMonth, MONTH_NAMES, monthBounds, observedYears } from "../lib/seriesTransforms";
import { useAuthStore } from "../stores/authStore";
import type { DateRange, SeriesParams } from "../types/analytics";

interface ChartCardProps {
  title: string;
  description: string;
  loading?: boolean;
  children: ReactNode;
}

function ChartCard({ title, description, loading, children }: ChartCardProps) {
  return (
    <Card className="min-w-0">
      <div className="mb-5 flex items-start justify-between gap-4">
        <div>
          <h2 className="text-lg font-semibold">{title}</h2>
          <p className="text-sm text-terminal-muted">{description}</p>
        </div>
        {loading && <Spinner label="Actualizando" />}
      </div>
      {children}
    </Card>
  );
}

export function DashboardPage() {
  const userId = useAuthStore((state) => state.user?.id_usuario ?? null);
  const [range, setRange] = useState<DateRange>({});
  const [selection, setSelection] = useState<SeriesSelection>({ view: "general", measure: "ingresos" });
  const enabled = userId !== null;
  const rangeKey = [range.fecha_desde ?? null, range.fecha_hasta ?? null];

  const global = useQuery({
    queryKey: ["analytics", userId, "global", ...rangeKey],
    queryFn: () => getGlobalStats(range),
    enabled,
  });
  const categories = useQuery({
    queryKey: ["analytics", userId, "categories", ...rangeKey],
    queryFn: () => getCategoryStats(range),
    enabled,
  });
  // The full list, unfiltered by dates, fixes each category's color and the comparison set.
  const allCategories = useQuery({
    queryKey: ["analytics", userId, "categories", null, null],
    queryFn: () => getCategoryStats({}),
    enabled,
  });

  const ranked = [...(allCategories.data?.analisis_por_categoria ?? [])].sort(
    (a, b) => b.ingresos_totales - a.ingresos_totales,
  );
  const categoryNames = ranked.map((row) => row.categoria);
  // More than eight lines cannot keep distinct colors, so the comparison keeps the top eight.
  const comparedCategories = categoryNames.slice(0, SERIES_COLORS.length);
  const view = selection.view;
  const categoria = view === "categoria" ? (selection.categoria ?? categoryNames[0]) : selection.categoria;

  const seriesQuery = (params: SeriesParams, active: boolean) => ({
    queryKey: ["analytics", userId, "series", params] as const,
    queryFn: () => getSalesSeries(params),
    enabled: enabled && active,
  });
  const monthly = useQuery(
    seriesQuery({ granularidad: "mes", categoria, ...range }, view !== "categoria" || categoria !== undefined),
  );
  const byCategory = useQuery(seriesQuery({ granularidad: "mes", por_categoria: true, ...range }, view === "categoria"));

  const points = monthly.data?.puntos ?? [];
  const years = observedYears(points);
  const latest = latestMonth(points);
  const year = selection.year !== undefined && years.includes(selection.year) ? selection.year : latest?.year;
  const month = selection.month ?? latest?.month;
  const daily = useQuery(
    seriesQuery(
      { granularidad: "dia", categoria, ...(year && month ? monthBounds(year, month, range) : {}) },
      view === "mes" && year !== undefined && month !== undefined,
    ),
  );

  const firstError = global.error ?? categories.error ?? monthly.error ?? byCategory.error ?? daily.error;
  const metrics = global.data?.metricas_globales;
  const subject = categoria ?? "Todas las categorías";
  const comparisonPoints = (byCategory.data?.puntos ?? []).filter(
    (point) => point.categoria !== null && comparedCategories.includes(point.categoria),
  );

  return (
    <div className="grid min-w-0 gap-8">
      <header className="grid gap-2">
        <p className="font-mono text-sm text-terminal-amber">dashboard // resumen</p>
        <h1 className="text-3xl font-semibold">Tu operación en una mirada</h1>
        <p className="text-terminal-muted">Mide lo que pasó. Encuentra el siguiente movimiento.</p>
      </header>

      <DateRangeFilter onApply={setRange} onClear={() => setRange({})} value={range} />
      <p className="text-sm text-terminal-muted">
        Rango activo: {range.fecha_desde ? formatDate(range.fecha_desde) : "inicio"} –{" "}
        {range.fecha_hasta ? formatDate(range.fecha_hasta) : "última venta"}. Aplica a las tarjetas y a todos los gráficos.
      </p>
      {firstError && <Alert tone="error">{getApiErrorMessage(firstError, "No se pudieron cargar las métricas.")}</Alert>}

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
        <MetricCard currency label="Ingresos totales" loading={global.isLoading} value={metrics?.total_ingresos} />
        <MetricCard label="Operaciones" loading={global.isLoading} value={metrics?.cantidad_operaciones} />
        <MetricCard currency label="Ticket promedio" loading={global.isLoading} value={metrics?.ticket_promedio} />
        <MetricCard currency label="Venta más alta" loading={global.isLoading} value={metrics?.venta_mas_alta} />
        <GrowthCard growth={global.data?.crecimiento_mensual} loading={global.isLoading} />
      </div>

      <SeriesViewSelector
        categories={categoryNames}
        onChange={(patch) => setSelection((current) => ({ ...current, ...patch }))}
        value={{ ...selection, categoria, year, month }}
        years={years}
      />

      {view === "general" && (
        <ChartCard
          description={`${subject}. Una línea por año para comparar las mismas temporadas.`}
          loading={monthly.isFetching}
          title="Años superpuestos"
        >
          <YearOverlayChart label={subject} measure={selection.measure} points={points} />
        </ChartCard>
      )}

      {view === "categoria" && (
        <>
          <ChartCard
            description="Una línea por año para la categoría elegida."
            loading={monthly.isFetching}
            title={`Años superpuestos: ${subject}`}
          >
            <YearOverlayChart label={subject} measure={selection.measure} points={points} />
          </ChartCard>
          <ChartCard
            description={
              categoryNames.length > comparedCategories.length
                ? `Las ${comparedCategories.length} categorías con más ingresos, mes a mes.`
                : "Todas las categorías, mes a mes."
            }
            loading={byCategory.isFetching}
            title="Comparación entre categorías"
          >
            <CategoryComparisonChart
              allCategories={comparedCategories}
              measure={selection.measure}
              points={comparisonPoints}
            />
          </ChartCard>
          <ChartCard
            description="Ingresos acumulados de cada categoría en el rango."
            loading={categories.isFetching}
            title="Ingresos por categoría"
          >
            <CategoryBarChart data={categories.data?.analisis_por_categoria ?? []} />
          </ChartCard>
        </>
      )}

      {view === "mes" && year !== undefined && month !== undefined && (
        <>
          <ChartCard
            description={`${subject}. Elige una barra para ver sus días.`}
            loading={monthly.isFetching}
            title={`Totales mensuales de ${year}`}
          >
            <MonthTotalsChart
              measure={selection.measure}
              onSelectMonth={(selected) => setSelection((current) => ({ ...current, year, month: selected }))}
              points={points}
              selectedMonth={month}
              year={year}
            />
          </ChartCard>
          <ChartCard
            description={`${subject}. Los días sin ventas quedan vacíos.`}
            loading={daily.isFetching}
            title={`Detalle diario: ${MONTH_NAMES[month - 1]} ${year}`}
          >
            <MonthDetailChart measure={selection.measure} month={month} points={daily.data?.puntos ?? []} year={year} />
          </ChartCard>
        </>
      )}

      {view === "historial" && (
        <ChartCard
          description={`${subject}. Todos los meses en una sola línea.`}
          loading={monthly.isFetching}
          title="Historial completo"
        >
          <HistoryLineChart measure={selection.measure} points={points} />
        </ChartCard>
      )}
    </div>
  );
}
