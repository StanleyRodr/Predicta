import { useEffect, useId, useRef, useState } from "react";

interface InfoHintProps {
  /** What the hint explains; names the button for screen readers. */
  label: string;
  children: string;
}

/** An "i" button that shows an explanation on click, Enter or Space, and hides it with Escape or a click outside. */
export function InfoHint({ label, children }: InfoHintProps) {
  const [open, setOpen] = useState(false);
  const panelId = useId();
  const rootRef = useRef<HTMLSpanElement>(null);
  const buttonRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (!open) return;
    function onPointerDown(event: PointerEvent) {
      if (!rootRef.current?.contains(event.target as Node)) setOpen(false);
    }
    document.addEventListener("pointerdown", onPointerDown);
    return () => document.removeEventListener("pointerdown", onPointerDown);
  }, [open]);

  return (
    <span
      className="relative inline-flex"
      onKeyDown={(event) => {
        if (event.key === "Escape" && open) {
          event.stopPropagation();
          setOpen(false);
          buttonRef.current?.focus();
        }
      }}
      ref={rootRef}
    >
      <button
        aria-controls={panelId}
        aria-expanded={open}
        aria-label={`Qué significa ${label}`}
        className="inline-flex size-5 items-center justify-center rounded-full border border-terminal-border font-mono text-xs text-terminal-muted hover:text-terminal-text"
        onClick={() => setOpen((value) => !value)}
        ref={buttonRef}
        type="button"
      >
        i
      </button>
      <span
        className="absolute left-0 top-7 z-10 w-64 rounded-md border border-terminal-border bg-terminal-surface p-3 text-xs leading-5 text-terminal-text shadow-lg"
        hidden={!open}
        id={panelId}
        role="note"
      >
        {children}
      </span>
    </span>
  );
}
