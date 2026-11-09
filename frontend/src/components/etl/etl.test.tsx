import { fireEvent, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import type { ColumnAnalysis, ColumnMapping } from "../../types/etl";
import { ColumnMappingPanel, mappingFromAnalysis, mappingProblem } from "./ColumnMappingPanel";
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

const EMPTY = { columna: null, origen: null, candidatos: [] };

const ANALYSIS: ColumnAnalysis = {
  columnas: ["item", "total", "importe", "fecha"],
  muestra: [{ item: "Pan", total: "10", importe: "12", fecha: "2026-01-05" }],
  propuesta: {
    producto: { columna: "item", origen: "sinonimo", candidatos: [] },
    categoria: EMPTY,
    monto: { columna: null, origen: null, candidatos: ["total", "importe"] },
    precio_unitario: EMPTY,
    cantidad: EMPTY,
    fecha: { columna: "fecha", origen: "exacto", candidatos: [] },
  },
  faltantes: ["monto"],
};

describe("ColumnMappingPanel", () => {
  it("preloads the proposal with its origin badges and tied candidates", () => {
    render(<ColumnMappingPanel analysis={ANALYSIS} onChange={vi.fn()} value={mappingFromAnalysis(ANALYSIS)} />);
    const panel = within(screen.getByRole("group", { name: "Mapeo de columnas" }));

    expect(panel.getByRole("combobox", { name: "Columna para Producto" })).toHaveValue("item");
    expect(panel.getByRole("combobox", { name: "Columna para Monto" })).toHaveValue("");
    expect(panel.getByText("Sinónimo")).toBeInTheDocument();
    expect(panel.getByText("Exacto")).toBeInTheDocument();
    expect(panel.getByText(/Hay varias columnas posibles: total, importe/)).toBeInTheDocument();
    expect(panel.getByRole("columnheader", { name: "Producto" })).toBeInTheDocument();
    expect(panel.getByRole("columnheader", { name: "importe" })).toBeInTheDocument();
  });

  it("reports the chosen column and removes it on Sin asignar", async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();
    const value: ColumnMapping = { producto: "item", fecha: "fecha" };
    render(<ColumnMappingPanel analysis={ANALYSIS} onChange={onChange} value={value} />);

    await user.selectOptions(screen.getByRole("combobox", { name: "Columna para Monto" }), "total");
    expect(onChange).toHaveBeenLastCalledWith({ producto: "item", fecha: "fecha", monto: "total" });

    await user.selectOptions(screen.getByRole("combobox", { name: "Columna para Producto" }), "");
    expect(onChange).toHaveBeenLastCalledWith({ fecha: "fecha" });
  });

  it("explains what blocks the upload", () => {
    expect(mappingProblem({ producto: "item", monto: "total" })).toBe("Falta asignar: Fecha.");
    expect(mappingProblem({ producto: "item", fecha: "fecha" })).toBe("Falta asignar: Monto o Precio unitario.");
    expect(mappingProblem({ producto: "item", monto: "item", fecha: "fecha" })).toBe("La columna item está asignada a dos roles.");
    expect(mappingProblem({ producto: "item", precio_unitario: "total", fecha: "fecha" })).toBeNull();
  });
});
