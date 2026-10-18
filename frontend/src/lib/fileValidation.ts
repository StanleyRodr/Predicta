export const MAX_UPLOAD_BYTES = 25 * 1024 * 1024;
export const ALLOWED_UPLOAD_EXTENSIONS = ["csv", "xlsx", "sql"] as const;

export function validateSalesFile(file: File | null): string | null {
  if (!file) return "Selecciona un archivo de ventas.";
  const extension = file.name.split(".").pop()?.toLowerCase();
  if (!extension || !ALLOWED_UPLOAD_EXTENSIONS.includes(extension as (typeof ALLOWED_UPLOAD_EXTENSIONS)[number])) {
    return "Formato no compatible. Usa CSV, XLSX o SQL.";
  }
  if (file.size > MAX_UPLOAD_BYTES) {
    return "El archivo supera el limite de 25 MB.";
  }
  return null;
}
