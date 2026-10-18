import type { ReactNode } from "react";

interface EmptyStateProps {
  title: string;
  description?: string;
  action?: ReactNode;
}

export function EmptyState({ title, description, action }: EmptyStateProps) {
  return (
    <div className="grid min-h-40 place-items-center rounded-lg border border-dashed border-terminal-border p-6 text-center">
      <div className="grid gap-2">
        <h2 className="font-semibold text-terminal-text">{title}</h2>
        {description && <p className="text-sm text-terminal-muted">{description}</p>}
        {action}
      </div>
    </div>
  );
}
