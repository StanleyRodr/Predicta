import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { getCategoryStats } from "../api/analytics";
import { downloadReport, reportErrorMessage } from "../api/reports";
import { Alert, Button, Card, Spinner } from "../components/ui";
import { useAuthStore } from "../stores/authStore";

const months = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"];

const selectClass = "min-h-11 rounded-md border border-terminal-border bg-terminal-bg px-3 text-terminal-text disabled:opacity-50";

export function ReportsPage() {
  const userId = useAuthStore((state) => state.user?.id_usuario ?? null);
  const [month, setMonth] = useState("enero");
  const [chosenCategory, setChosenCategory] = useState<string | null>(null);
  const [downloading, setDownloading] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Same query and key as the other pages, so the list is shared from the cache.
  const categories = useQuery({
    queryKey: ["analytics", userId, "categories", null, null],
    queryFn: () => getCategoryStats({}),
    enabled: userId !== null,
  });
  const names = (categories.data?.analisis_por_categoria ?? [])
    .map((row) => row.categoria)
    .sort((a, b) => a.localeCompare(b, "es"));
  // The first category until the user picks one that still exists.
  const category = chosenCategory !== null && names.includes(chosenCategory) ? chosenCategory : (names[0] ?? "");

  async function download(key: string, path: string, fallback: string) {
    setDownloading(key);
    setError(null);
    try {
      await downloadReport(path, fallback);
    } catch (reason) {
      setError(await reportErrorMessage(reason));
    } finally {
      setDownloading(null);
    }
  }

  return (
    <div className="grid gap-8">
      <header className="grid gap-2">
        <p className="font-mono text-sm text-terminal-amber">salidas // reportes</p>
        <h1 className="text-3xl font-semibold">Reportes operativos</h1>
        <p className="text-terminal-muted">Descarga resultados para compartirlos o revisarlos fuera de Predicta.</p>
      </header>
      {error && <Alert tone="error">{error}</Alert>}
      <div className="grid gap-4 md:grid-cols-2">
        <ReportCard busy={downloading === "excel"} description="Historial completo en formato de hoja de cálculo." label="Reporte Excel" onClick={() => download("excel", "/analytics/export/excel", "reporte-ventas.xlsx")} />
        <ReportCard busy={downloading === "pdf"} description="Historial y evolución diaria en PDF." label="Reporte PDF" onClick={() => download("pdf", "/analytics/export/pdf", "reporte-ventas.pdf")} />
        <ReportCard busy={downloading === "annual"} description="Historial y proyección de los próximos 12 meses." label="Proyección anual" onClick={() => download("annual", "/analytics/reporte-predictivo-anual-pdf", "reporte-anual.pdf")} />
        <Card className="grid gap-4">
          <div className="grid gap-1"><h2 className="font-semibold">Reporte mensual</h2><p className="text-sm text-terminal-muted">Compara un mes futuro con su historial.</p></div>
          <select aria-label="Mes del reporte" className={selectClass} onChange={(event) => setMonth(event.target.value)} value={month}>{months.map((item) => <option key={item}>{item}</option>)}</select>
          <Button disabled={downloading === "month"} onClick={() => download("month", `/analytics/reporte-mensual/${month}`, `reporte-${month}.pdf`)}>{downloading === "month" ? <Spinner label="Descargando" /> : "Descargar mensual"}</Button>
        </Card>
        <Card className="grid gap-4">
          <div className="grid gap-1"><h2 className="font-semibold">Reporte por categoría</h2><p className="text-sm text-terminal-muted">Proyecta una de tus categorías.</p></div>
          <select
            aria-label="Categoría del reporte"
            className={selectClass}
            disabled={!names.length}
            onChange={(event) => setChosenCategory(event.target.value)}
            value={category}
          >
            {names.map((name) => (
              <option key={name} value={name}>
                {name}
              </option>
            ))}
          </select>
          {categories.isLoading && <Spinner label="Cargando categorías" />}
          {categories.isSuccess && !names.length && (
            <p className="text-sm text-terminal-muted">Todavía no hay categorías. Carga ventas para generar este reporte.</p>
          )}
          {categories.error && <Alert tone="error">No se pudieron cargar las categorías.</Alert>}
          <Button disabled={!category || downloading === "category"} onClick={() => download("category", `/analytics/prediccion-categorias/${encodeURIComponent(category)}`, "reporte-categoria.pdf")}>{downloading === "category" ? <Spinner label="Descargando" /> : "Descargar categoría"}</Button>
        </Card>
      </div>
    </div>
  );
}

function ReportCard({ label, description, onClick, busy }: { label: string; description: string; onClick: () => void; busy: boolean }) {
  return <Card className="grid gap-4"><div className="grid gap-1"><h2 className="font-semibold">{label}</h2><p className="text-sm text-terminal-muted">{description}</p></div><Button disabled={busy} onClick={onClick}>{busy ? <Spinner label="Descargando" /> : "Descargar"}</Button></Card>;
}
