import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { clearSalesHistory, uploadSales } from "../api/etl";
import { getSalesHistory } from "../api/sales";
import { SalesHistoryTable, UploadDropzone, UploadSummary } from "../components/etl";
import { Alert, Button, Card, Modal, Spinner } from "../components/ui";
import { getApiErrorMessage } from "../lib/apiErrors";

const PAGE_SIZE = 10;

export function UploadPage() {
  const queryClient = useQueryClient();
  const [file, setFile] = useState<File | null>(null);
  const [page, setPage] = useState(1);
  const [isClearModalOpen, setIsClearModalOpen] = useState(false);
  const [clientError, setClientError] = useState<string | null>(null);

  const history = useQuery({
    queryKey: ["sales-history", page],
    queryFn: () => getSalesHistory((page - 1) * PAGE_SIZE, PAGE_SIZE),
  });
  const upload = useMutation({
    mutationFn: (selectedFile: File) => uploadSales(selectedFile),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["sales-history"] });
      setFile(null);
      setClientError(null);
    },
  });
  const clear = useMutation({
    mutationFn: clearSalesHistory,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["sales-history"] });
      setPage(1);
      setIsClearModalOpen(false);
    },
  });

  function selectFile(selectedFile: File) {
    setFile(selectedFile);
    setClientError(null);
    upload.reset();
  }

  function submitUpload() {
    if (!file) {
      setClientError("Selecciona un archivo antes de cargarlo.");
      return;
    }
    upload.mutate(file);
  }

  const error = clientError ?? (upload.error ? getApiErrorMessage(upload.error, "No se pudo procesar el archivo.") : null);
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
        {file && (
          <div className="flex flex-wrap items-center justify-between gap-4 rounded-md border border-terminal-border bg-terminal-bg p-3">
            <span className="truncate font-mono text-sm text-terminal-text">{file.name}</span>
            <Button disabled={upload.isPending} onClick={submitUpload}>
              {upload.isPending ? <Spinner label="Procesando" /> : "Cargar archivo"}
            </Button>
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
