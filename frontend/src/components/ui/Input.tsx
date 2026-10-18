import type { InputHTMLAttributes } from "react";
import { cn } from "../../lib/cn";

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
}

export function Input({ className, label, error, id, ...props }: InputProps) {
  return (
    <label className="grid gap-2 text-sm text-terminal-muted" htmlFor={id}>
      {label}
      <input
        id={id}
        className={cn(
          "min-h-11 rounded-md border bg-terminal-bg px-3 font-mono text-terminal-text placeholder:text-terminal-muted/60",
          "border-terminal-border focus:border-terminal-amber focus:outline-none",
          error && "border-terminal-error",
          className,
        )}
        aria-invalid={Boolean(error)}
        aria-describedby={error && id ? `${id}-error` : undefined}
        {...props}
        />
      {error && (
        <span className="text-xs text-terminal-error" id={id ? `${id}-error` : undefined}>
          {error}
        </span>
      )}
    </label>
  );
}
