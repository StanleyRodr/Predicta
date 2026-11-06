import { useState } from "react";
import { downloadReport, reportErrorMessage } from "../api/reports";
import { Alert, Button, Card, Input, Spinner } from "../components/ui";

const months = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"];

export function ReportsPage() {
  const [month, setMonth] = useState("enero");
  const [category, setCategory] = useState("");
  const [downloading, setDownloading] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

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
        <ReportCard busy={downloading === "excel"} description="Historial completo en formato de hoja de calculo." label="Reporte Excel" onClick={() => download("excel", "/analytics/export/excel", "reporte-ventas.xlsx")} />
        <ReportCard busy={downloading === "pdf"} description="Historial y evolucion diaria en PDF." label="Reporte PDF" onClick={() => download("pdf", "/analytics/export/pdf", "reporte-ventas.pdf")} />
        <ReportCard busy={downloading === "annual"} description="Historial y proyeccion de los proximos 12 meses." label="Proyeccion anual" onClick={() => download("annual", "/analytics/reporte-predictivo-anual-pdf", "reporte-anual.pdf")} />
        <Card className="grid gap-4">
          <div className="grid gap-1"><h2 className="font-semibold">Reporte mensual</h2><p className="text-sm text-terminal-muted">Compara un mes futuro con su historial.</p></div>
          <select aria-label="Mes del reporte" className="min-h-11 rounded-md border border-terminal-border bg-terminal-bg px-3 text-terminal-text" onChange={(event) => setMonth(event.target.value)} value={month}>{months.map((item) => <option key={item}>{item}</option>)}</select>
          <Button disabled={downloading === "month"} onClick={() => download("month", `/analytics/reporte-mensual/${month}`, `reporte-${month}.pdf`)}>{downloading === "month" ? <Spinner label="Descargando" /> : "Descargar mensual"}</Button>
        </Card>
        <Card className="grid gap-4">
          <div className="grid gap-1"><h2 className="font-semibold">Reporte por categoria</h2><p className="text-sm text-terminal-muted">Proyecta una categoria especifica.</p></div>
          <Input aria-label="Categoria del reporte" label="Categoria" onChange={(event) => setCategory(event.target.value)} placeholder="Abarrotes" value={category} />
          <Button disabled={!category.trim() || downloading === "category"} onClick={() => download("category", `/analytics/prediccion-categorias/${encodeURIComponent(category.trim())}`, "reporte-categoria.pdf")}>{downloading === "category" ? <Spinner label="Descargando" /> : "Descargar categoria"}</Button>
        </Card>
      </div>
    </div>
  );
}

function ReportCard({ label, description, onClick, busy }: { label: string; description: string; onClick: () => void; busy: boolean }) {
  return <Card className="grid gap-4"><div className="grid gap-1"><h2 className="font-semibold">{label}</h2><p className="text-sm text-terminal-muted">{description}</p></div><Button disabled={busy} onClick={onClick}>{busy ? <Spinner label="Descargando" /> : "Descargar"}</Button></Card>;
}
