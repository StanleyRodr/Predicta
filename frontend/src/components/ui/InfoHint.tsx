import { useEffect, useId, useLayoutEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";

interface InfoHintProps {
  /** What the hint explains; names the button for screen readers. */
  label: string;
  children: string;
}

interface Box {
  top: number;
  left: number;
  width: number;
  height: number;
}

/** Space kept between the panel, its button, and the screen edges. */
const GAP = 8;
const EDGE = 16;

/**
 * Where the panel goes, in viewport coordinates: below the button, or above it
 * when it does not fit, and always inside the screen.
 */
export function placeHint(button: Box, panel: { width: number; height: number }, viewport: { width: number; height: number }) {
  const below = button.top + button.height + GAP;
  const above = button.top - GAP - panel.height;
  const top = below + panel.height <= viewport.height - EDGE || above < EDGE ? below : above;
  const left = Math.min(Math.max(button.left, EDGE), Math.max(EDGE, viewport.width - panel.width - EDGE));
  return { top, left };
}

/**
 * An "i" button that shows an explanation on click, Enter or Space, and hides it
 * with Escape or a click outside. The panel floats on the page body, so no
 * scrolling container clips it or grows scrollbars around it.
 */
export function InfoHint({ label, children }: InfoHintProps) {
  const [open, setOpen] = useState(false);
  const [position, setPosition] = useState<{ top: number; left: number } | null>(null);
  const panelId = useId();
  const buttonRef = useRef<HTMLButtonElement>(null);
  const panelRef = useRef<HTMLSpanElement>(null);

  // Follow the button while the page or any container scrolls.
  useLayoutEffect(() => {
    if (!open) {
      setPosition(null);
      return;
    }
    function place() {
      const button = buttonRef.current;
      const panel = panelRef.current;
      if (!button || !panel) return;
      setPosition(
        placeHint(button.getBoundingClientRect(), panel.getBoundingClientRect(), {
          width: window.innerWidth,
          height: window.innerHeight,
        }),
      );
    }
    place();
    window.addEventListener("scroll", place, true);
    window.addEventListener("resize", place);
    return () => {
      window.removeEventListener("scroll", place, true);
      window.removeEventListener("resize", place);
    };
  }, [open]);

  useEffect(() => {
    if (!open) return;
    function onPointerDown(event: PointerEvent) {
      const target = event.target as Node;
      if (!buttonRef.current?.contains(target) && !panelRef.current?.contains(target)) setOpen(false);
    }
    function onKeyDown(event: KeyboardEvent) {
      if (event.key !== "Escape") return;
      event.stopPropagation();
      setOpen(false);
      buttonRef.current?.focus();
    }
    document.addEventListener("pointerdown", onPointerDown);
    document.addEventListener("keydown", onKeyDown);
    return () => {
      document.removeEventListener("pointerdown", onPointerDown);
      document.removeEventListener("keydown", onKeyDown);
    };
  }, [open]);

  return (
    <span className="inline-flex">
      <button
        aria-controls={open ? panelId : undefined}
        aria-expanded={open}
        aria-label={`Qué significa ${label}`}
        className="inline-flex size-5 items-center justify-center rounded-full border border-terminal-border font-mono text-xs text-terminal-muted hover:text-terminal-text"
        onClick={() => setOpen((value) => !value)}
        ref={buttonRef}
        type="button"
      >
        i
      </button>
      {open &&
        createPortal(
          <span
            className="fixed z-50 w-64 max-w-[calc(100vw-2rem)] rounded-md border border-terminal-border bg-terminal-surface p-3 text-left text-xs font-normal leading-5 text-terminal-text shadow-lg"
            id={panelId}
            ref={panelRef}
            role="note"
            // Hidden until measured, so it never flashes at the wrong place.
            style={open && position ? { top: position.top, left: position.left } : { top: 0, left: 0, visibility: "hidden" }}
          >
            {children}
          </span>,
          document.body,
        )}
    </span>
  );
}
