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
  UploadBatchTable,
  UploadDropzone,
  UploadSummary,
  type BatchRow,
} from "../components/etl";
import { Alert, Button, Card, Modal, Spinner } from "../components/ui";
import { getApiErrorMessage } from "../lib/apiErrors";
import { validateSalesFile } from "../lib/fileValidation";
import { refreshSalesData } from "../lib/salesCache";
import { fileStatus, groupByHeaders, headerKey, sortFiles } from "../lib/uploadBatch";
import { useAuthStore } from "../stores/authStore";
import type { ColumnAnalysis, ColumnMapping } from "../types/etl";

const PAGE_SIZE = 10;

interface BatchItem extends BatchRow {
  file: File;
  analysis?: ColumnAnalysis;
}

type AnalyzedItem = BatchItem & { analysis: ColumnAnalysis };
type BatchPhase = "analizando" | "listo" | "cargando" | "terminado";

function isAnalyzed(item: BatchItem): item is AnalyzedItem {
  return item.analysis !== undefined;
}

function replaceItem(items: BatchItem[], next: BatchItem): BatchItem[] {
  return items.map((item) => (item.file === next.file ? next : item));
}

function groupTitle(items: BatchItem[]): string {
  if (items.length === 1) return `1 archivo: ${items[0].name}`;
  return `${items.length} archivos: ${items[0].name} … ${items[items.length - 1].name}`;
}

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
  // Several files: each keeps its own analysis and result; files with the same
  // headers share one mapping. A new selection makes every pending answer stale.
  const [batch, setBatch] = useState<BatchItem[] | null>(null);
  const [groupMappings, setGroupMappings] = useState<Record<string, ColumnMapping>>({});
  const [batchPhase, setBatchPhase] = useState<BatchPhase>("listo");
  const [progress, setProgress] = useState({ done: 0, total: 0 });
  const selection = useRef(0);

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
    selection.current += 1;
    setBatch(null);
    setBatchPhase("listo");
    currentFile.current = selectedFile;
    setFile(selectedFile);
    setMapping(null);
    setClientError(null);
    upload.reset();
    analysis.reset();
    analysis.mutate(selectedFile);
  }

  async function selectFiles(selectedFiles: File[]) {
    const id = ++selection.current;
    currentFile.current = null;
    setFile(null);
    setMapping(null);
    setClientError(null);
    upload.reset();
    analysis.reset();

    let items: BatchItem[] = sortFiles(selectedFiles).map((selectedFile): BatchItem => {
      const invalid = validateSalesFile(selectedFile);
      return invalid
        ? { file: selectedFile, name: selectedFile.name, status: "No válido", message: invalid }
        : { file: selectedFile, name: selectedFile.name, status: "Pendiente" };
    });
    const pending = items.filter((item) => item.status === "Pendiente");
    setBatch(items);
    setGroupMappings({});
    setBatchPhase("analizando");
    setProgress({ done: 0, total: pending.length });

    for (const [index, item] of pending.entries()) {
      let next: BatchItem;
      try {
        next = { ...item, analysis: await analyzeColumns(item.file) };
      } catch (analysisFailure) {
        next = { ...item, status: "Error al analizar", message: getApiErrorMessage(analysisFailure, "No se pudo analizar el archivo.") };
      }
      if (selection.current !== id) return;
      items = replaceItem(items, next);
      setBatch(items);
      setProgress({ done: index + 1, total: pending.length });
    }

    const mappings: Record<string, ColumnMapping> = {};
    for (const group of groupByHeaders(items.filter(isAnalyzed))) {
      mappings[group.key] = mappingFromAnalysis(group.items[0].analysis);
    }
    setGroupMappings(mappings);
    setBatchPhase("listo");
  }

  async function uploadBatch() {
    if (!batch) return;
    const id = selection.current;
    const targets = batch.filter(isAnalyzed);
    let items = batch;
    setBatchPhase("cargando");
    setProgress({ done: 0, total: targets.length });

    for (const [index, item] of targets.entries()) {
      let next: BatchItem;
      try {
        const result = await uploadSales(item.file, groupMappings[headerKey(item.analysis)]);
        next = { ...item, status: "Cargado", result, message: undefined };
      } catch (uploadFailure) {
        next = { ...item, status: fileStatus(uploadFailure), message: getApiErrorMessage(uploadFailure, "No se pudo procesar el archivo.") };
      }
      if (selection.current !== id) return;
      items = replaceItem(items, next);
      setBatch(items);
      setProgress({ done: index + 1, total: targets.length });
    }

    await refreshSalesData(queryClient);
    setBatchPhase("terminado");
  }

  const batchGroups = batch ? groupByHeaders(batch.filter(isAnalyzed)) : [];
  const batchProblems = batchGroups.map((group) => {
    const groupMapping = groupMappings[group.key];
    return groupMapping ? mappingProblem(groupMapping) : null;
  });
  const canUploadBatch =
    batchPhase === "listo" &&
    batchGroups.length > 0 &&
    batchGroups.every((group) => groupMappings[group.key]) &&
    batchProblems.every((problem) => problem === null);

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
        <UploadDropzone
          disabled={upload.isPending || batchPhase === "cargando"}
          onFileSelected={selectFile}
          onFilesSelected={selectFiles}
        />
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
        {batch && (
          <div className="grid gap-5">
            <div className="flex flex-wrap items-center justify-between gap-4 rounded-md border border-terminal-border bg-terminal-bg p-3">
              <span className="font-mono text-sm text-terminal-text">
                {batchPhase === "analizando" && `Analizando ${progress.done} de ${progress.total}`}
                {batchPhase === "cargando" && `Cargando ${progress.done} de ${progress.total}`}
                {batchPhase === "listo" && `${batch.length} archivos seleccionados`}
                {batchPhase === "terminado" && `Carga terminada: ${progress.total} archivos procesados`}
              </span>
              {batchPhase === "analizando" || batchPhase === "cargando" ? (
                <Spinner label={batchPhase === "analizando" ? "Analizando columnas" : "Procesando"} />
              ) : (
                <Button disabled={!canUploadBatch} onClick={uploadBatch}>
                  Cargar ventas
                </Button>
              )}
            </div>
            {batchPhase !== "analizando" &&
              batchGroups.map((group, index) => {
                const groupMapping = groupMappings[group.key];
                if (!groupMapping) return null;
                const title = groupTitle(group.items);
                return (
                  <section aria-label={`Mapeo para ${title}`} className="grid gap-3" key={group.key}>
                    <h2 className="font-mono text-sm text-terminal-amber">{title}</h2>
                    <ColumnMappingPanel
                      analysis={group.items[0].analysis}
                      onChange={(next) => setGroupMappings((current) => ({ ...current, [group.key]: next }))}
                      value={groupMapping}
                    />
                    {batchProblems[index] && <p className="text-sm text-terminal-amber">{batchProblems[index]}</p>}
                  </section>
                );
              })}
            <UploadBatchTable rows={batch} />
          </div>
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
