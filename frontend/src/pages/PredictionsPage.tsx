import { useQuery } from "@tanstack/react-query";
import { isAxiosError } from "axios";
import { useState } from "react";
import { getForecast } from "../api/forecast";
import { ForecastMetricCard, ForecastQuality } from "../components/forecast";
import { Alert, Button, Card, Spinner } from "../components/ui";
import { getApiErrorMessage } from "../lib/apiErrors";
import { formatDate } from "../lib/formatters";
import { useAuthStore } from "../stores/authStore";

/** 422 means the history cannot support a forecast yet; it is not a failure. */
function isUnprocessable(error: unknown): boolean {
  return isAxiosError(error) && error.response?.status === 422;
}

export function PredictionsPage() {
  const userId = useAuthStore((state) => state.user?.id_usuario ?? null);
  const [requested, setRequested] = useState(false);
  const forecast = useQuery({
    queryKey: ["forecast", userId],
    queryFn: getForecast,
    enabled: false,
    refetchOnWindowFocus: false,
    staleTime: Infinity,
    // Asking again cannot add sales history.
    retry: (failures, error) => !isUnprocessable(error) && failures < 1,
  });

  async function calculate() {
    setRequested(true);
    await forecast.refetch();
  }

  const available = forecast.data;
  const insufficient = isUnprocessable(forecast.error);

  return (
    <div className="grid gap-8">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div className="grid gap-2">
          <p className="font-mono text-sm text-terminal-amber">ml // proyeccion</p>
          <h1 className="text-3xl font-semibold">Siguiente movimiento</h1>
          <p className="text-terminal-muted">Calcula una proyeccion diaria sin confundir estimacion con garantia.</p>
        </div>
        <Button disabled={forecast.isFetching} onClick={calculate}>
          {forecast.isFetching ? <Spinner label="Calculando" /> : "Calcular prediccion"}
        </Button>
      </header>
      {!requested && <Card><p className="text-terminal-muted">La prediccion se ejecuta solo cuando la solicitas.</p></Card>}
      {forecast.error && insufficient && (
        <Alert tone="info">
          {getApiErrorMessage(forecast.error, "Todavía no hay suficientes ventas para proyectar.")} Carga más días de ventas y vuelve a intentarlo.
        </Alert>
      )}
      {forecast.error && !insufficient && (
        <Alert tone="error">{getApiErrorMessage(forecast.error, "No se pudo calcular la predicción.")}</Alert>
      )}
      {available && (
        <>
          <div className="grid gap-4 sm:grid-cols-2">
            <ForecastMetricCard interval={available.intervalos_prediccion.monto} label="Monto predicho" value={available.monto_predicho} />
            <ForecastMetricCard interval={available.intervalos_prediccion.cantidad} label="Cantidad predicha" quantity value={available.cantidad_predicha} />
          </div>
          <p className="text-sm text-terminal-muted">Fecha proyectada: <span className="font-mono text-terminal-text">{formatDate(available.proxima_fecha)}</span></p>
          <ForecastQuality amount={available.metricas.monto} quantity={available.metricas.cantidad} />
          <Alert tone="info">{available.mensaje}</Alert>
        </>
      )}
    </div>
  );
}
