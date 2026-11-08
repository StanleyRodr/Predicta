import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import { InfoHint } from "./InfoHint";

function renderHint() {
  render(
    <div>
      <InfoHint label="error promedio">Cuánto se equivoca en promedio.</InfoHint>
      <button type="button">Fuera</button>
    </div>,
  );
  return screen.getByRole("button", { name: "Qué significa error promedio" });
}

describe("InfoHint", () => {
  it("starts closed and is linked to its explanation", () => {
    const button = renderHint();

    expect(button).toHaveAttribute("aria-expanded", "false");
    expect(screen.queryByRole("note")).not.toBeInTheDocument();
    expect(document.getElementById(button.getAttribute("aria-controls") ?? "")).toHaveTextContent("Cuánto se equivoca en promedio.");
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
