import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useState } from "react";
import { describe, expect, it, vi } from "vitest";
import { Modal } from "./Modal";

function Harness({ onClose = () => undefined }: { onClose?: () => void }) {
  const [open, setOpen] = useState(false);
  return (
    <>
      <button onClick={() => setOpen(true)} type="button">
        Abrir
      </button>
      <Modal
        onClose={() => {
          onClose();
          setOpen(false);
        }}
        open={open}
        title="Purgar historial"
      >
        <button type="button">Confirmar</button>
      </Modal>
    </>
  );
}

describe("Modal", () => {
  it("closes with Escape and returns the focus to the button that opened it", async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();
    render(<Harness onClose={onClose} />);
    const opener = screen.getByRole("button", { name: "Abrir" });

    await user.click(opener);
    expect(screen.getByRole("dialog", { name: "Purgar historial" })).toHaveFocus();

    await user.keyboard("{Escape}");
    expect(onClose).toHaveBeenCalledOnce();
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    expect(opener).toHaveFocus();
  });

  it("keeps Tab and Shift+Tab inside the dialog", async () => {
    const user = userEvent.setup();
    render(<Harness />);
    await user.click(screen.getByRole("button", { name: "Abrir" }));
    const close = screen.getByRole("button", { name: "Cerrar" });
    const confirm = screen.getByRole("button", { name: "Confirmar" });

    await user.tab();
    expect(close).toHaveFocus();
    await user.tab();
    expect(confirm).toHaveFocus();
    await user.tab();
    expect(close).toHaveFocus();
    await user.tab({ shift: true });
    expect(confirm).toHaveFocus();
  });

  it("gives each dialog its own title id", () => {
    render(
      <>
        <Modal onClose={() => undefined} open title="Primero">
          uno
        </Modal>
        <Modal onClose={() => undefined} open title="Segundo">
          dos
        </Modal>
      </>,
    );

    const first = screen.getByRole("dialog", { name: "Primero" });
    const second = screen.getByRole("dialog", { name: "Segundo" });
    expect(first.getAttribute("aria-labelledby")).not.toBe(second.getAttribute("aria-labelledby"));
  });
});
