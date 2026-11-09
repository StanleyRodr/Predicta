import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { isAxiosError } from "axios";
import { useState } from "react";
import { getCategoryStats } from "../api/analytics";
import { getForecast, getMonthlyForecast, listSavedPredictions, savePrediction } from "../api/forecast";
import { CategoryProductFilter, type CategoryProduct } from "../components/analytics";
import {
  ConceptHint,
  FORECAST_MEASURES,
  ForecastChart,
  ForecastMetricCard,
  ForecastQuality,
  ForecastTable,
  formatForecastValue,
  MonthDetail,
  SavedPredictions,
  type ForecastMeasure,
  type ForecastRow,
} from "../components/forecast";
import { Alert, Button, Card, Segmented, Spinner } from "../components/ui";
import { getApiErrorMessage } from "../lib/apiErrors";
import { MODEL_NAMES } from "../lib/conceptExplanations";
import { formatDate } from "../lib/formatters";
import { periodLabel } from "../lib/seriesTransforms";
import { useAuthStore } from "../stores/authStore";
import type { MonthlyForecastResponse } from "../types/forecast";

/** 422 means the history cannot support a forecast yet; it is not a failure. */
function isUnprocessable(error: unknown): boolean {
  return isAxiosError(error) && error.response?.status === 422;
}

const forecastQuery = {
  refetchOnWindowFocus: false,
  staleTime: Infinity,
  // Asking again cannot add sales history.
  retry: (failures: number, error: Error) => !isUnprocessable(error) && failures < 1,
};

function projectionRows(forecast: MonthlyForecastResponse, measure: ForecastMeasure): ForecastRow[] {
  return forecast.proyeccion.map((month) => ({
    periodo: month.periodo,
    monto: month.monto.prediccion,
    cantidad: month.cantidad.prediccion,
    inferior: month[measure].inferior,
    superior: month[measure].superior,
    extrapolacion: month.extrapolacion,
  }));
}

function ForecastProblem({ error, fallback }: { error: unknown; fallback: string }) {
  if (isUnprocessable(error)) {
    return (
      <Alert tone="info">
        {getApiErrorMessage(error, "Todavía no hay suficientes ventas para proyectar.")} Carga más ventas y vuelve a intentarlo.
      </Alert>
    );
  }
  return <Alert tone="error">{getApiErrorMessage(error, fallback)}</Alert>;
}

export function PredictionsPage() {
  const userId = useAuthStore((state) => state.user?.id_usuario ?? null);
  const queryClient = useQueryClient();
  const [scope, setScope] = useState<CategoryProduct>({ categoria: "", producto: "" });
  // The scope of the last "Calcular proyección"; changing the selectors alone fetches nothing.
  const [requested, setRequested] = useState<CategoryProduct | null>(null);
  const [measure, setMeasure] = useState<ForecastMeasure>("monto");
  const [selected, setSelected] = useState<string | null>(null);
  const categoria = requested?.categoria || undefined;
  const producto = (categoria && requested?.producto) || undefined;

  const categories = useQuery({
    queryKey: ["analytics", userId, "categories", null, null],
    queryFn: () => getCategoryStats({}),
    enabled: userId !== null,
  });
  const monthly = useQuery({
    queryKey: ["forecast", userId, "mensual", categoria ?? null, producto ?? null],
    queryFn: () => getMonthlyForecast(categoria, producto),
    enabled: requested !== null,
    ...forecastQuery,
  });
  // A product is compared with its category and a category with the total, to warn when their models differ.
  const referenceCategory = producto ? categoria : undefined;
  const total = useQuery({
    queryKey: ["forecast", userId, "mensual", referenceCategory ?? null, null],
    queryFn: () => getMonthlyForecast(referenceCategory),
    enabled: categoria !== undefined,
    ...forecastQuery,
  });
  const daily = useQuery({
    queryKey: ["forecast", userId, "diaria"],
    queryFn: getForecast,
    enabled: requested !== null,
    ...forecastQuery,
  });
  const saved = useQuery({
    queryKey: ["saved-predictions", userId],
    queryFn: () => listSavedPredictions(0, 10),
    enabled: userId !== null,
  });
  const save = useMutation({
    mutationFn: () => savePrediction(categoria, producto),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["saved-predictions", userId] }),
  });

  function calculate() {
    save.reset();
    if (requested?.categoria === scope.categoria && requested.producto === scope.producto) {
      void monthly.refetch();
      void daily.refetch();
      if (scope.categoria) void total.refetch();
    }
    setRequested(scope);
  }

  const forecast = monthly.data;
  const current = forecast?.proyeccion.find((month) => month.periodo === selected) ?? forecast?.proyeccion[0];
  const reference = total.data;
  const modelsDiffer =
    categoria !== undefined &&
    forecast !== undefined &&
    reference !== undefined &&
    (forecast.modelo !== reference.modelo || forecast.horizonte_aplicado !== reference.horizonte_aplicado);
  const calculating = monthly.isFetching || daily.isFetching;
  const names = [...(categories.data?.analisis_por_categoria ?? [])]
    .sort((a, b) => b.ingresos_totales - a.ingresos_totales)
    .map((row) => row.categoria);

  return (
    <div className="grid min-w-0 gap-8">
      <header className="grid gap-2">
        <p className="font-mono text-sm text-terminal-amber">ml // proyección</p>
        <h1 className="text-3xl font-semibold">Siguiente movimiento</h1>
        <p className="text-terminal-muted">
          Estima los próximos meses con su margen de incertidumbre, en general, por categoría o por producto.
        </p>
      </header>

      <Card className="flex flex-wrap items-end gap-3">
        <CategoryProductFilter
          allCategoriesLabel="General: todas las categorías"
          categories={names}
          categoryLabel="Alcance"
          onChange={setScope}
          value={scope}
        />
        <Button disabled={calculating} onClick={calculate}>
          {calculating ? <Spinner label="Calculando" /> : "Calcular proyección"}
        </Button>
      </Card>

      {requested === null && (
        <Card>
          <p className="text-terminal-muted">La proyección se calcula solo cuando la solicitas. Consultarla no guarda nada.</p>
        </Card>
      )}
      {monthly.error && <ForecastProblem error={monthly.error} fallback="No se pudo calcular la proyección." />}

      {forecast && current && (
        <>
          <Card className="grid min-w-0 gap-5">
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div className="grid gap-1">
                <h2 className="text-lg font-semibold">
                  {forecast.producto
                    ? `Proyección de ${forecast.producto} (${forecast.categoria})`
                    : forecast.categoria
                      ? `Proyección de ${forecast.categoria}`
                      : "Proyección de todas las categorías"}
                </h2>
                <p className="flex flex-wrap items-center gap-x-1.5 text-sm text-terminal-muted">
                  {forecast.horizonte_aplicado} meses con {MODEL_NAMES[forecast.modelo]} <ConceptHint concept="modelo" />, a partir de{" "}
                  {forecast.meses_observados} meses completos.
                </p>
                <p className="flex flex-wrap items-center gap-x-1.5 text-sm text-terminal-muted">
                  La zona sombreada es el intervalo del 95 % <ConceptHint concept="intervalo" />: el valor real probablemente caerá
                  dentro de esta zona.
                </p>
              </div>
              <Segmented label="Medida" onChange={setMeasure} options={FORECAST_MEASURES} value={measure} />
            </div>
            {forecast.advertencias.length > 0 && (
              <Alert className="grid gap-2" tone="info">
                <p className="flex items-center gap-2 font-medium text-terminal-text">
                  Toma esta proyección con cautela <ConceptHint concept="cautela" />
                </p>
                <ul className="grid list-disc gap-1 pl-5">
                  {forecast.advertencias.map((reason) => (
                    <li key={reason}>{reason}</li>
                  ))}
                </ul>
              </Alert>
            )}
            {modelsDiffer && reference && forecast.producto && (
              <Alert tone="info">
                Este producto usa {MODEL_NAMES[forecast.modelo]} con {forecast.horizonte_aplicado} meses, y su categoría usa{" "}
                {MODEL_NAMES[reference.modelo]} con {reference.horizonte_aplicado} meses: las proyecciones por producto no suman
                exactamente la categoría.
              </Alert>
            )}
            {modelsDiffer && reference && !forecast.producto && (
              <Alert tone="info">
                Esta categoría usa {MODEL_NAMES[forecast.modelo]} con {forecast.horizonte_aplicado} meses, y el total usa{" "}
                {MODEL_NAMES[reference.modelo]} con {reference.horizonte_aplicado} meses: las proyecciones por categoría no suman
                exactamente el total.
              </Alert>
            )}
            <ForecastChart forecast={forecast} measure={measure} onSelect={setSelected} selected={current.periodo} />
            {forecast.proyeccion.some((month) => month.extrapolacion) && (
              <p className="flex flex-wrap items-center gap-x-1.5 text-sm text-terminal-muted">
                Los rombos huecos y el trazo más fino marcan extrapolación <ConceptHint concept="extrapolacion" />: meses que tu
                historial no permite validar.
              </p>
            )}
            {forecast.mes_parcial && (
              <p className="flex flex-wrap items-center gap-x-1.5 text-sm text-terminal-muted">
                El punto hueco es el mes en curso, {periodLabel(forecast.mes_parcial.periodo)} <ConceptHint concept="mesParcial" />:
                lleva {formatForecastValue(measure, forecast.mes_parcial[measure])} hasta ahora y se proyecta completo.
              </p>
            )}
          </Card>

          <MonthDetail month={current} />

          <Card className="grid gap-4">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <h2 className="font-semibold">Detalle mensual</h2>
              <Button disabled={save.isPending} onClick={() => save.mutate()} variant="ghost">
                {save.isPending ? <Spinner label="Guardando" /> : "Guardar proyección"}
              </Button>
            </div>
            {save.isSuccess && (
              <Alert tone="success">Proyección guardada: {save.data.puntos.length} meses. La encuentras en la lista de abajo.</Alert>
            )}
            {save.error && <Alert tone="error">{getApiErrorMessage(save.error, "No se pudo guardar la proyección.")}</Alert>}
            <ForecastTable
              caption="Meses proyectados"
              measure={measure}
              onSelect={setSelected}
              rows={projectionRows(forecast, measure)}
              selected={current.periodo}
            />
          </Card>

          <ForecastQuality amount={forecast.metricas.monto} history={forecast.historial} quantity={forecast.metricas.cantidad} />
        </>
      )}

      {requested !== null && (
        <section aria-label="Proyección del día siguiente" className="grid gap-4">
          <h2 className="font-semibold">Mañana, todas las categorías</h2>
          {daily.error && <ForecastProblem error={daily.error} fallback="No se pudo calcular el día siguiente." />}
          {daily.data && (
            <>
              <div className="grid gap-4 sm:grid-cols-2">
                <ForecastMetricCard interval={daily.data.intervalos_prediccion.monto} label="Monto predicho" value={daily.data.monto_predicho} />
                <ForecastMetricCard
                  interval={daily.data.intervalos_prediccion.cantidad}
                  label="Cantidad predicha"
                  quantity
                  value={daily.data.cantidad_predicha}
                />
              </div>
              <p className="text-sm text-terminal-muted">
                Fecha proyectada: <span className="font-mono text-terminal-text">{formatDate(daily.data.proxima_fecha)}</span>
              </p>
            </>
          )}
        </section>
      )}

      <section aria-label="Proyecciones guardadas" className="grid gap-4">
        <h2 className="flex items-center gap-2 font-semibold">
          Proyecciones guardadas <ConceptHint concept="guardadas" />
        </h2>
        {saved.error && <Alert tone="error">{getApiErrorMessage(saved.error, "No se pudieron cargar las proyecciones guardadas.")}</Alert>}
        {saved.data && <SavedPredictions batches={saved.data.lotes} />}
      </section>
    </div>
  );
}
