import { describe, expect, it } from "vitest";
import { MAX_UPLOAD_BYTES, validateSalesFile } from "./fileValidation";

function file(name: string, size = 10) {
  return new File([new Uint8Array(size)], name, { type: "text/plain" });
}

describe("sales file validation", () => {
  it("accepts supported extensions under 25 MB", () => {
    expect(validateSalesFile(file("ventas.csv"))).toBeNull();
    expect(validateSalesFile(file("ventas.XLSX"))).toBeNull();
    expect(validateSalesFile(file("ventas.sql"))).toBeNull();
  });

  it("rejects empty, unsupported, and oversized files", () => {
    expect(validateSalesFile(null)).toContain("Selecciona");
    expect(validateSalesFile(file("ventas.pdf"))).toContain("Formato");
    expect(validateSalesFile(file("ventas.csv", MAX_UPLOAD_BYTES + 1))).toContain("25 MB");
  });
});
