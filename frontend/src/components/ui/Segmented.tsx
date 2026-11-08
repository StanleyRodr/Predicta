import { cn } from "../../lib/cn";

interface SegmentedProps<T extends string> {
  label: string;
  options: Record<T, string>;
  value: T;
  onChange: (value: T) => void;
}

/** A row of mutually exclusive choices, announced as a radio group. */
export function Segmented<T extends string>({ label, options, value, onChange }: SegmentedProps<T>) {
  return (
    <div aria-label={label} className="flex flex-wrap gap-1 rounded-lg border border-terminal-border p-1" role="radiogroup">
      {(Object.keys(options) as T[]).map((key) => (
        <button
          aria-checked={value === key}
          className={cn(
            "rounded-md px-3 py-1.5 text-sm transition-colors",
            value === key ? "bg-terminal-amber font-medium text-terminal-bg" : "text-terminal-muted hover:text-terminal-text",
          )}
          key={key}
          onClick={() => onChange(key)}
          role="radio"
          type="button"
        >
          {options[key]}
        </button>
      ))}
    </div>
  );
}
