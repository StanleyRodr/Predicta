import { AxiosError, type AxiosResponse } from "axios";
import { afterEach, describe, expect, it, vi } from "vitest";
import { downloadReport, reportErrorMessage } from "./reports";
import { http } from "./http";

afterEach(() => {
  vi.useRealTimers();
  vi.restoreAllMocks();
});

function errorWithBody(data: unknown): AxiosError {
  return new AxiosError("failed", undefined, undefined, undefined, { status: 400, data } as AxiosResponse);
}

// jsdom's Blob does not implement text(), which every supported browser has.
function blobWithText(content: string): Blob {
  return Object.assign(new Blob([content]), { text: () => Promise.resolve(content) });
}

describe("report downloads", () => {
  it("uses server filename, creates a blob URL, and revokes it later", async () => {
    vi.useFakeTimers();
    const blob = new Blob(["report"]);
    vi.spyOn(http, "get").mockResolvedValue({
      data: blob,
      headers: { "content-disposition": "attachment; filename=ventas%20enero.xlsx" },
    } as never);
    const create = vi.spyOn(URL, "createObjectURL").mockReturnValue("blob:test");
    const revoke = vi.spyOn(URL, "revokeObjectURL").mockImplementation(() => undefined);
    const click = vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(() => undefined);

    await downloadReport("/analytics/export/excel", "fallback.xlsx");

    expect(http.get).toHaveBeenCalledWith("/analytics/export/excel", { responseType: "blob", timeout: 120_000 });
    expect(create).toHaveBeenCalledWith(blob);
    expect(click).toHaveBeenCalledOnce();
    expect(revoke).not.toHaveBeenCalled();

    vi.runAllTimers();

    expect(revoke).toHaveBeenCalledWith("blob:test");
  });
});

describe("reportErrorMessage", () => {
  it("reads the backend detail from a Blob body", async () => {
    const body = blobWithText(JSON.stringify({ detail: "Muestreo insuficiente para analisis lineal." }));

    await expect(reportErrorMessage(errorWithBody(body))).resolves.toBe("Muestreo insuficiente para analisis lineal.");
  });

  it("falls back when the Blob is not JSON", async () => {
    await expect(reportErrorMessage(errorWithBody(blobWithText("<html>")))).resolves.toBe("No se pudo descargar el reporte.");
  });

  it("keeps the connection message when there is no response", async () => {
    await expect(reportErrorMessage(new AxiosError("Network Error"))).resolves.toContain("No se puede conectar");
  });
});
