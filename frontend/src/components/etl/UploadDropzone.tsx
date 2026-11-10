import { useRef, useState } from "react";
import { Alert } from "../ui/Alert";
import { cn } from "../../lib/cn";
import { validateSalesFile } from "../../lib/fileValidation";
import { MAX_BATCH_FILES, TOO_MANY_FILES } from "../../lib/uploadBatch";

interface UploadDropzoneProps {
  /** One file, already validated. */
  onFileSelected: (file: File) => void;
  /** Several files, unvalidated: the page lists the invalid ones with their reason. */
  onFilesSelected?: (files: File[]) => void;
  disabled?: boolean;
}

export function UploadDropzone({ onFileSelected, onFilesSelected, disabled = false }: UploadDropzoneProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function selectFile(file: File | undefined) {
    const validationError = validateSalesFile(file ?? null);
    setError(validationError);
    if (!validationError && file) onFileSelected(file);
  }

  function selectFiles(list: FileList | null | undefined) {
    const files = Array.from(list ?? []);
    if (files.length <= 1 || !onFilesSelected) {
      selectFile(files[0]);
      return;
    }
    if (files.length > MAX_BATCH_FILES) {
      setError(TOO_MANY_FILES);
      return;
    }
    setError(null);
    onFilesSelected(files);
  }

  return (
    <div className="grid gap-3">
      <button
        className={cn(
          "grid min-h-48 place-items-center rounded-lg border-2 border-dashed p-6 text-center transition-colors",
          "border-terminal-border bg-terminal-bg hover:border-terminal-amber",
          isDragging && "border-terminal-amber bg-terminal-amber/5",
          disabled && "cursor-not-allowed opacity-50",
        )}
        disabled={disabled}
        onClick={() => inputRef.current?.click()}
        onDragEnter={(event) => {
          event.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDragOver={(event) => event.preventDefault()}
        onDrop={(event) => {
          event.preventDefault();
          setIsDragging(false);
          selectFiles(event.dataTransfer.files);
        }}
        type="button"
      >
        <span className="grid gap-2">
          <strong className="font-mono text-terminal-amber">+ cargar archivo</strong>
          <span className="text-sm text-terminal-muted">
            {onFilesSelected ? "Arrastra aqui o selecciona uno o varios archivos CSV, XLSX o SQL" : "Arrastra aqui o selecciona CSV, XLSX o SQL"}
          </span>
          <span className="font-mono text-xs text-terminal-muted">
            {onFilesSelected ? `max 25 MB por archivo, hasta ${MAX_BATCH_FILES} archivos` : "max 25 MB"}
          </span>
        </span>
      </button>
      <input
        accept=".csv,.xlsx,.sql"
        aria-label="Seleccionar archivo"
        className="sr-only"
        disabled={disabled}
        multiple={Boolean(onFilesSelected)}
        onChange={(event) => {
          selectFiles(event.target.files);
          // Choosing the same files again must still fire onChange.
          event.target.value = "";
        }}
        ref={inputRef}
        type="file"
      />
      {error && <Alert tone="error">{error}</Alert>}
    </div>
  );
}
