import { fireEvent, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import type { UploadResult } from "../../types/etl";
import { UploadBatchTable, type BatchRow } from "./UploadBatchTable";
import { UploadDropzone } from "./UploadDropzone";

function csv(name: string): File {
  return new File(["data"], name, { type: "text/csv" });
}

function dropzone() {
  return screen.getByRole("button", { name: /cargar archivo/i });
}

describe("UploadDropzone with several files", () => {
  it("hands every dropped file to onFilesSelected", () => {
    const onFileSelected = vi.fn();
    const onFilesSelected = vi.fn();
    render(<UploadDropzone onFileSelected={onFileSelected} onFilesSelected={onFilesSelected} />);
    const files = [csv("a.csv"), csv("b.csv"), csv("c.csv")];

    fireEvent.drop(dropzone(), { dataTransfer: { files } });

    expect(onFilesSelected).toHaveBeenCalledWith(files);
    expect(onFileSelected).not.toHaveBeenCalled();
  });

  it("lets the file picker choose several files", () => {
    render(<UploadDropzone onFileSelected={vi.fn()} onFilesSelected={vi.fn()} />);

    expect(screen.getByLabelText("Seleccionar archivo")).toHaveAttribute("multiple");
  });

  it("keeps a single dropped file on the one-file path", () => {
    const onFileSelected = vi.fn();
    const onFilesSelected = vi.fn();
    render(<UploadDropzone onFileSelected={onFileSelected} onFilesSelected={onFilesSelected} />);
    const file = csv("ventas.csv");

    fireEvent.drop(dropzone(), { dataTransfer: { files: [file] } });

    expect(onFileSelected).toHaveBeenCalledWith(file);
    expect(onFilesSelected).not.toHaveBeenCalled();
  });

  it("refuses more than 50 files at once", () => {
    const onFilesSelected = vi.fn();
    render(<UploadDropzone onFileSelected={vi.fn()} onFilesSelected={onFilesSelected} />);
    const files = Array.from({ length: 51 }, (_, index) => csv(`v${index}.csv`));

    fireEvent.change(screen.getByLabelText("Seleccionar archivo"), { target: { files } });

    expect(onFilesSelected).not.toHaveBeenCalled();
    expect(screen.getByRole("alert")).toHaveTextContent("Puedes cargar hasta 50 archivos a la vez.");
  });

  it("passes an unsupported file along with the others so the page can list it", () => {
    const onFilesSelected = vi.fn();
    render(<UploadDropzone onFileSelected={vi.fn()} onFilesSelected={onFilesSelected} />);
    const files = [csv("a.csv"), new File(["x"], "notas.txt"), csv("b.csv")];

    fireEvent.drop(dropzone(), { dataTransfer: { files } });

    expect(onFilesSelected).toHaveBeenCalledWith(files);
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });
});

function result(leidos: number, cargados: number): UploadResult {
  return {
    message: "Procesamiento exitoso",
    registros_leidos: leidos,
    registros_cargados: cargados,
    filas_rechazadas: leidos - cargados,
    errores: leidos > cargados ? [{ fila: 2, error: "la cantidad no puede ser negativa" }] : [],
  };
}

const ROWS: BatchRow[] = [
  { name: "v_2012.csv", status: "Cargado", result: result(1000, 990) },
  { name: "v_2013.csv", status: "Ya cargado", message: "Este archivo ya fue cargado." },
  { name: "v_2014.csv", status: "Cargado", result: result(2500, 2500) },
  { name: "notas.txt", status: "No válido", message: "Formato no compatible. Usa CSV, XLSX o SQL." },
];

describe("UploadBatchTable", () => {
  it("lists every file with its status, counts or message", () => {
    render(<UploadBatchTable rows={ROWS} />);
    const table = within(screen.getByRole("table", { name: "Archivos seleccionados" }));

    const loaded = within(table.getByRole("row", { name: /v_2012\.csv/ }));
    expect(loaded.getByText("Cargado")).toBeInTheDocument();
    expect(loaded.getByText("1,000")).toBeInTheDocument();
    expect(loaded.getByText("990")).toBeInTheDocument();

    const duplicate = within(table.getByRole("row", { name: /v_2013\.csv/ }));
    expect(duplicate.getByText("Ya cargado")).toBeInTheDocument();
    expect(duplicate.getByText("Este archivo ya fue cargado.")).toBeInTheDocument();

    expect(within(table.getByRole("row", { name: /notas\.txt/ })).getByText("No válido")).toBeInTheDocument();
  });

  it("adds up only the loaded files", () => {
    render(<UploadBatchTable rows={ROWS} />);
    const total = within(screen.getByRole("row", { name: /^Total/ }));

    expect(total.getByText("2 de 4 cargados")).toBeInTheDocument();
    expect(total.getByText("3,500")).toBeInTheDocument();
    expect(total.getByText("3,490")).toBeInTheDocument();
    expect(total.getByText("10")).toBeInTheDocument();
  });

  it("shows the summary of a loaded file on demand", async () => {
    const user = userEvent.setup();
    render(<UploadBatchTable rows={ROWS} />);

    await user.click(screen.getByRole("button", { name: "Ver detalle de v_2012.csv" }));

    const detail = within(screen.getByRole("region", { name: "Detalle de v_2012.csv" }));
    expect(detail.getByText("la cantidad no puede ser negativa")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Ver detalle de v_2012.csv" }));
    expect(screen.queryByRole("region", { name: "Detalle de v_2012.csv" })).not.toBeInTheDocument();
  });
});
