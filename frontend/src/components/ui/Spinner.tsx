interface SpinnerProps {
  label?: string;
}

export function Spinner({ label = "Cargando" }: SpinnerProps) {
  return (
    <span className="inline-flex items-center gap-2 text-sm text-terminal-muted" role="status">
      <span className="size-4 animate-spin rounded-full border-2 border-terminal-border border-t-terminal-amber" />
      {label}
    </span>
  );
}
