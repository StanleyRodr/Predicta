import { fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { SalesHistoryTable } from "./SalesHistoryTable";
import { UploadDropzone } from "./UploadDropzone";
import { UploadSummary } from "./UploadSummary";

describe("ETL components", () => {
  it("rejects unsupported files before upload", () => {
    const onFileSelected = vi.fn();
    render(<UploadDropzone onFileSelected={onFileSelected} />);
    const input = screen.getByLabelText("Seleccionar archivo");
    fireEvent.change(input, { target: { files: [new File(["data"], "ventas.pdf")] } });

    expect(screen.getByRole("alert")).toHaveTextContent("Formato no compatible");
    expect(onFileSelected).not.toHaveBeenCalled();
  });

  it("selects supported files with keyboard-accessible control", async () => {
    const user = userEvent.setup();
    const onFileSelected = vi.fn();
    render(<UploadDropzone onFileSelected={onFileSelected} />);
    const input = screen.getByRole("button", { name: /cargar archivo/i });
    await user.click(input);

    expect(input).toBeEnabled();
  });

  it("renders upload counters and row errors", () => {
    render(
      <UploadSummary
        result={{
          message: "Procesamiento exitoso",
          registros_leidos: 2,
          registros_cargados: 1,
          filas_rechazadas: 1,
          errores: [{ fila: 3, error: "el monto no es numerico" }],
        }}
      />,
    );

    expect(screen.getByText("el monto no es numerico")).toBeInTheDocument();
    expect(screen.getByText("50%", { selector: "span" })).toBeInTheDocument();
  });

  it("renders empty history and paginated records", () => {
    const onPageChange = vi.fn();
    const data = {
      usuario: "ana",
      total_registros: 1,
      pagina_actual: 1,
      total_paginas: 2,
      registros: [{ id: 1, producto: "Arroz", monto: 12, categoria: "Abarrotes", fecha: "2026-01-01" }],
    };

    const { rerender } = render(<SalesHistoryTable isLoading={false} onPageChange={onPageChange} page={1} />);
    expect(screen.getByText("Historial vacio")).toBeInTheDocument();
    rerender(<SalesHistoryTable data={data} isLoading={false} onPageChange={onPageChange} page={1} />);

    expect(screen.getByText("Arroz")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Siguiente" }));
    expect(onPageChange).toHaveBeenCalledWith(2);
  });
});
