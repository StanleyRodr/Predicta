import { afterEach, describe, expect, it, vi } from "vitest";
import { downloadReport } from "./reports";
import { http } from "./http";

afterEach(() => vi.restoreAllMocks());

describe("report downloads", () => {
  it("uses server filename, creates a blob URL, and revokes it", async () => {
    const blob = new Blob(["report"]);
    vi.spyOn(http, "get").mockResolvedValue({
      data: blob,
      headers: { "content-disposition": "attachment; filename=ventas%20enero.xlsx" },
    } as never);
    const create = vi.spyOn(URL, "createObjectURL").mockReturnValue("blob:test");
    const revoke = vi.spyOn(URL, "revokeObjectURL").mockImplementation(() => undefined);
    const click = vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(() => undefined);

    await downloadReport("/analytics/export/excel", "fallback.xlsx");

    expect(http.get).toHaveBeenCalledWith("/analytics/export/excel", { responseType: "blob" });
    expect(create).toHaveBeenCalledWith(blob);
    expect(click).toHaveBeenCalledOnce();
    expect(revoke).toHaveBeenCalledWith("blob:test");
  });
});
