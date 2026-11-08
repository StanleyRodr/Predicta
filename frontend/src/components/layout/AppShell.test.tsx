import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";
import { AppShell } from "./AppShell";

function renderShell() {
  render(
    <MemoryRouter initialEntries={["/dashboard"]}>
      <AppShell />
    </MemoryRouter>,
  );
  return screen.getByRole("button", { name: "Abrir menú de navegación" });
}

describe("AppShell mobile menu", () => {
  it("names the menu buttons instead of showing MENU and X", async () => {
    const user = userEvent.setup();
    const toggle = renderShell();

    expect(toggle).toHaveAttribute("aria-expanded", "false");
    expect(document.getElementById(toggle.getAttribute("aria-controls") ?? "")).toHaveAccessibleName("Menú lateral");

    await user.click(toggle);
    expect(toggle).toHaveAttribute("aria-expanded", "true");
    expect(toggle).toHaveAccessibleName("Cerrar menú de navegación");
    expect(screen.queryByRole("button", { name: "X" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "MENU" })).not.toBeInTheDocument();
  });

  it("closes with Escape or the close button and returns the focus", async () => {
    const user = userEvent.setup();
    const toggle = renderShell();

    await user.click(toggle);
    await user.keyboard("{Escape}");
    expect(toggle).toHaveAttribute("aria-expanded", "false");
    expect(toggle).toHaveFocus();

    await user.click(toggle);
    const [close] = screen.getAllByRole("button", { name: "Cerrar menú de navegación" }).filter((button) => button !== toggle);
    await user.click(close);
    expect(toggle).toHaveAttribute("aria-expanded", "false");
    expect(toggle).toHaveFocus();
  });
});
