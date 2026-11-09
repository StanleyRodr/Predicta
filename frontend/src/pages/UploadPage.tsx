import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useRef, useState } from "react";
import { getCategoryStats } from "../api/analytics";
import { analyzeColumns, clearSalesHistory, uploadSales } from "../api/etl";
import { getSalesHistory } from "../api/sales";
import { CategoryProductFilter, type CategoryProduct } from "../components/analytics";
import {
  ColumnMappingPanel,
  mappingFromAnalysis,
  mappingProblem,
  SalesHistoryTable,
  UploadDropzone,
  UploadSummary,
} from "../components/etl";
import { Alert, Button, Card, Modal, Spinner } from "../components/ui";
import { getApiErrorMessage } from "../lib/apiErrors";
import { refreshSalesData } from "../lib/salesCache";
import { useAuthStore } from "../stores/authStore";
import type { ColumnMapping } from "../types/etl";

const PAGE_SIZE = 10;

export function UploadPage() {
  const queryClient = useQueryClient();
  const userId = useAuthStore((state) => state.user?.id_usuario ?? null);
  const [file, setFile] = useState<File | null>(null);
  const currentFile = useRef<File | null>(null);
  const [mapping, setMapping] = useState<ColumnMapping | null>(null);
  const [page, setPage] = useState(1);
  const [filter, setFilter] = useState<CategoryProduct>({ categoria: "", producto: "" });
  const [isClearModalOpen, setIsClearModalOpen] = useState(false);
  const [clientError, setClientError] = useState<string | null>(null);

  const categories = useQuery({
    queryKey: ["analytics", userId, "categories", null, null],
    queryFn: () => getCategoryStats({}),
    enabled: userId !== null,
  });
  const history = useQuery({
    queryKey: ["sales-history", userId, page, filter.categoria, filter.producto],
    queryFn: () => getSalesHistory((page - 1) * PAGE_SIZE, PAGE_SIZE, filter.categoria, filter.producto),
    enabled: userId !== null,
  });
  const categoryNames = (categories.data?.analisis_por_categoria ?? [])
    .map((row) => row.categoria)
    .sort((a, b) => a.localeCompare(b, "es"));

  function changeFilter(next: CategoryProduct) {
    setFilter(next);
    setPage(1);
  }
  const analysis = useMutation({
    mutationFn: async (selectedFile: File) => ({ file: selectedFile, result: await analyzeColumns(selectedFile) }),
    onSuccess: ({ file: analyzed, result }) => {
      // A slow answer for a file the user already replaced must not overwrite the new one.
      if (analyzed === currentFile.current) setMapping(mappingFromAnalysis(result));
    },
  });
  const upload = useMutation({
    mutationFn: ({ selectedFile, mapeo }: { selectedFile: File; mapeo: ColumnMapping }) => uploadSales(selectedFile, mapeo),
    onSuccess: async () => {
      await refreshSalesData(queryClient);
      currentFile.current = null;
      setFile(null);
      setMapping(null);
      analysis.reset();
      setClientError(null);
    },
  });
  const clear = useMutation({
    mutationFn: clearSalesHistory,
    onSuccess: async () => {
      await refreshSalesData(queryClient);
      setPage(1);
      setIsClearModalOpen(false);
    },
  });

  function selectFile(selectedFile: File) {
    currentFile.current = selectedFile;
    setFile(selectedFile);
    setMapping(null);
    setClientError(null);
    upload.reset();
    analysis.reset();
    analysis.mutate(selectedFile);
  }

  const analyzed = analysis.data && analysis.data.file === file ? analysis.data.result : null;
  const problem = mapping ? mappingProblem(mapping) : null;

  function submitUpload() {
    if (!file || !mapping) {
      setClientError("Selecciona un archivo antes de cargarlo.");
      return;
    }
    upload.mutate({ selectedFile: file, mapeo: mapping });
  }

  const analysisError = analysis.error && analysis.variables === file ? getApiErrorMessage(analysis.error, "No se pudo analizar el archivo.") : null;
  const error =
    clientError ?? analysisError ?? (upload.error ? getApiErrorMessage(upload.error, "No se pudo procesar el archivo.") : null);
  const clearError = clear.error ? getApiErrorMessage(clear.error, "No se pudo limpiar el historial.") : null;

  return (
    <div className="grid gap-8">
      <header className="grid gap-2">
        <p className="font-mono text-sm text-terminal-amber">datos // importar</p>
        <h1 className="text-3xl font-semibold">Carga de ventas</h1>
        <p className="max-w-2xl text-terminal-muted">Carga tu historial y revisa cada fila aceptada o rechazada antes de analizarlo.</p>
      </header>

      <Card className="grid gap-5">
        <UploadDropzone disabled={upload.isPending} onFileSelected={selectFile} />
        <p className="text-sm text-terminal-muted">Escribe los montos como 1,234.56. Una coma seguida de 3 dígitos se lee como miles: 1,234 significa mil doscientos treinta y cuatro.</p>
        {file && (
          <div className="flex flex-wrap items-center justify-between gap-4 rounded-md border border-terminal-border bg-terminal-bg p-3">
            <span className="truncate font-mono text-sm text-terminal-text">{file.name}</span>
            {analysis.isPending ? (
              <Spinner label="Analizando columnas" />
            ) : (
              <Button disabled={upload.isPending || !analyzed || !mapping || problem !== null} onClick={submitUpload}>
                {upload.isPending ? <Spinner label="Procesando" /> : "Cargar ventas"}
              </Button>
            )}
          </div>
        )}
        {analyzed && mapping && (
          <>
            <ColumnMappingPanel analysis={analyzed} onChange={setMapping} value={mapping} />
            {problem && <p className="text-sm text-terminal-amber">{problem}</p>}
          </>
        )}
        {error && <Alert tone="error">{error}</Alert>}
        {upload.data && <UploadSummary result={upload.data} />}
      </Card>

      <section className="grid gap-4">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div className="grid gap-2">
            <p className="font-mono text-sm text-terminal-amber">movimientos // historial</p>
            <h2 className="text-2xl font-semibold">Ventas cargadas</h2>
          </div>
          <Button disabled={!history.data?.total_registros || clear.isPending} onClick={() => setIsClearModalOpen(true)} variant="danger">
            Purgar historial
          </Button>
        </div>
        <div className="flex flex-wrap items-end gap-3">
          <CategoryProductFilter categories={categoryNames} onChange={changeFilter} value={filter} />
        </div>
        {clearError && <Alert tone="error">{clearError}</Alert>}
        {history.error && <Alert tone="error">{getApiErrorMessage(history.error, "No se pudo cargar el historial.")}</Alert>}
        <SalesHistoryTable data={history.data} isLoading={history.isLoading} onPageChange={setPage} page={page} />
      </section>

      <Modal onClose={() => setIsClearModalOpen(false)} open={isClearModalOpen} title="Purgar historial">
        <div className="grid gap-5">
          <p className="text-sm leading-6 text-terminal-muted">Esta accion elimina todas tus ventas cargadas. No se puede deshacer.</p>
          <div className="flex justify-end gap-3">
            <Button onClick={() => setIsClearModalOpen(false)} variant="secondary">Cancelar</Button>
            <Button disabled={clear.isPending} onClick={() => clear.mutate()} variant="danger">
              {clear.isPending ? "Purgando" : "Confirmar purga"}
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
