import type { ReactNode } from "react";
import { Button } from "./Button";

interface ModalProps {
  open: boolean;
  title: string;
  children: ReactNode;
  onClose: () => void;
}

export function Modal({ open, title, children, onClose }: ModalProps) {
  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 grid place-items-center bg-black/70 p-4" role="presentation">
      <section
        aria-labelledby="modal-title"
        aria-modal="true"
        className="w-full max-w-lg rounded-lg border border-terminal-border bg-terminal-surface p-6"
        role="dialog"
      >
        <div className="flex items-start justify-between gap-4">
          <h2 className="text-lg font-semibold text-terminal-text" id="modal-title">
            {title}
          </h2>
          <Button aria-label="Cerrar" onClick={onClose} variant="ghost">
            X
          </Button>
        </div>
        <div className="mt-4">{children}</div>
      </section>
    </div>
  );
}
