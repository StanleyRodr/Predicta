import { AxiosError, AxiosHeaders } from "axios";
import { describe, expect, it } from "vitest";
import type { ColumnAnalysis, UploadResult } from "../types/etl";
import { batchTotals, fileStatus, groupByHeaders, sortFiles } from "./uploadBatch";

const EMPTY = { columna: null, origen: null, candidatos: [] };

function analysis(columnas: string[]): ColumnAnalysis {
  return {
    columnas,
    muestra: [],
    propuesta: { producto: EMPTY, categoria: EMPTY, monto: EMPTY, precio_unitario: EMPTY, cantidad: EMPTY, fecha: EMPTY },
    faltantes: [],
  };
}

function result(leidos: number, cargados: number): UploadResult {
  return { message: "ok", registros_leidos: leidos, registros_cargados: cargados, filas_rechazadas: leidos - cargados, errores: [] };
}

function httpError(status?: number): AxiosError {
  const config = { headers: new AxiosHeaders() };
  const response = status === undefined ? undefined : { status, statusText: "", headers: {}, config, data: {} };
  return new AxiosError("fail", undefined, config, undefined, response);
}

describe("sortFiles", () => {
  it("orders names naturally, so quarters and years read in time order", () => {
    const files = ["x_2010Q10.csv", "x_2010Q2.csv", "x_2009.csv"].map((name) => new File([""], name));

    expect(sortFiles(files).map((file) => file.name)).toEqual(["x_2009.csv", "x_2010Q2.csv", "x_2010Q10.csv"]);
  });

  it("does not reorder the array it receives", () => {
    const files = ["b.csv", "a.csv"].map((name) => new File([""], name));
    sortFiles(files);

    expect(files.map((file) => file.name)).toEqual(["b.csv", "a.csv"]);
  });
});

describe("groupByHeaders", () => {
  it("groups files with the same headers and separates extra or reordered columns", () => {
    const items = [
      { name: "a", analysis: analysis(["producto", "monto", "fecha"]) },
      { name: "b", analysis: analysis(["producto", "monto", "fecha"]) },
      { name: "c", analysis: analysis(["producto", "monto", "fecha", "categoria"]) },
      { name: "d", analysis: analysis(["monto", "producto", "fecha"]) },
    ];

    const groups = groupByHeaders(items);

    expect(groups.map((group) => group.items.map((item) => item.name))).toEqual([["a", "b"], ["c"], ["d"]]);
  });
});

describe("batchTotals", () => {
  it("adds only the files that were loaded", () => {
    expect(batchTotals([result(10, 8), undefined, result(5, 5)])).toEqual({ leidos: 15, cargados: 13, rechazados: 2 });
  });
});

describe("fileStatus", () => {
  it("reads a 409 as an already loaded file", () => {
    expect(fileStatus(httpError(409))).toBe("Ya cargado");
  });

  it.each([400, 500])("reads %i as an error", (status) => {
    expect(fileStatus(httpError(status))).toBe("Error");
  });

  it("reads a network failure or an unknown error as an error", () => {
    expect(fileStatus(httpError())).toBe("Error");
    expect(fileStatus(new Error("boom"))).toBe("Error");
  });
});
