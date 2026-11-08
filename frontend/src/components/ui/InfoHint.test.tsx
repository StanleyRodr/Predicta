import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import { InfoHint, placeHint } from "./InfoHint";

function renderHint() {
  render(
    <div data-testid="scroller" style={{ overflow: "auto", height: 40 }}>
      <InfoHint label="error promedio">Cuánto se equivoca en promedio.</InfoHint>
      <button type="button">Fuera</button>
    </div>,
  );
  return screen.getByRole("button", { name: "Qué significa error promedio" });
}

describe("placeHint", () => {
  const viewport = { width: 375, height: 600 };
  const panel = { width: 256, height: 100 };

  it("opens below the button", () => {
    expect(placeHint({ top: 100, left: 40, width: 20, height: 20 }, panel, viewport)).toEqual({ top: 128, left: 40 });
  });

  it("opens above the button when it does not fit below", () => {
    expect(placeHint({ top: 520, left: 40, width: 20, height: 20 }, panel, viewport)).toEqual({ top: 412, left: 40 });
  });

  it("stays below when it fits nowhere, so it never goes past the top", () => {
    expect(placeHint({ top: 50, left: 40, width: 20, height: 20 }, { width: 256, height: 590 }, viewport).top).toBe(78);
  });

  it("keeps 16 px from both screen edges", () => {
    expect(placeHint({ top: 100, left: 340, width: 20, height: 20 }, panel, viewport).left).toBe(375 - 256 - 16);
    expect(placeHint({ top: 100, left: 2, width: 20, height: 20 }, panel, viewport).left).toBe(16);
  });
});

describe("InfoHint", () => {
  it("starts closed and links the open panel to its button", async () => {
    const user = userEvent.setup();
    const button = renderHint();

    expect(button).toHaveAttribute("aria-expanded", "false");
    expect(screen.queryByRole("note")).not.toBeInTheDocument();

    await user.click(button);
    expect(document.getElementById(button.getAttribute("aria-controls") ?? "")).toHaveTextContent("Cuánto se equivoca en promedio.");
  });

  it("floats the panel on the page body, outside any scrolling container", async () => {
    const user = userEvent.setup();
    const button = renderHint();

    await user.click(button);
    const panel = screen.getByRole("note");

    expect(panel.parentElement).toBe(document.body);
    expect(screen.getByTestId("scroller")).not.toContainElement(panel);
    expect(panel).toHaveClass("fixed");
    expect(panel).toBeVisible();
  });

  it("stays open on a click inside the panel", async () => {
    const user = userEvent.setup();
    await user.click(renderHint());

    await user.click(screen.getByRole("note"));

    expect(screen.getByRole("note")).toBeInTheDocument();
  });

  it("opens with Enter and closes with Escape, keeping the focus", async () => {
    const user = userEvent.setup();
    const button = renderHint();

    await user.tab();
    expect(button).toHaveFocus();
    await user.keyboard("{Enter}");
    expect(button).toHaveAttribute("aria-expanded", "true");
    expect(screen.getByRole("note")).toHaveTextContent("Cuánto se equivoca en promedio.");

    await user.keyboard("{Escape}");
    expect(button).toHaveAttribute("aria-expanded", "false");
    expect(screen.queryByRole("note")).not.toBeInTheDocument();
    expect(button).toHaveFocus();
  });

  it("toggles with a click and closes on a click outside", async () => {
    const user = userEvent.setup();
    const button = renderHint();

    await user.click(button);
    expect(screen.getByRole("note")).toBeVisible();
    await user.click(screen.getByRole("button", { name: "Fuera" }));
    expect(screen.queryByRole("note")).not.toBeInTheDocument();

    await user.click(button);
    await user.click(button);
    expect(button).toHaveAttribute("aria-expanded", "false");
  });
});
