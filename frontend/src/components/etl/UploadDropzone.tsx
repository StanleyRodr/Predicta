import { useRef, useState } from "react";
import { Alert } from "../ui/Alert";
import { cn } from "../../lib/cn";
import { validateSalesFile } from "../../lib/fileValidation";

interface UploadDropzoneProps {
  onFileSelected: (file: File) => void;
  disabled?: boolean;
}

export function UploadDropzone({ onFileSelected, disabled = false }: UploadDropzoneProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function selectFile(file: File | undefined) {
    const validationError = validateSalesFile(file ?? null);
    setError(validationError);
    if (!validationError && file) onFileSelected(file);
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
          selectFile(event.dataTransfer.files[0]);
        }}
        type="button"
      >
        <span className="grid gap-2">
          <strong className="font-mono text-terminal-amber">+ cargar archivo</strong>
          <span className="text-sm text-terminal-muted">Arrastra aqui o selecciona CSV, XLSX o SQL</span>
          <span className="font-mono text-xs text-terminal-muted">max 25 MB</span>
        </span>
      </button>
      <input
        accept=".csv,.xlsx,.sql"
        aria-label="Seleccionar archivo"
        className="sr-only"
        disabled={disabled}
        onChange={(event) => selectFile(event.target.files?.[0])}
        ref={inputRef}
        type="file"
      />
      {error && <Alert tone="error">{error}</Alert>}
    </div>
  );
}
