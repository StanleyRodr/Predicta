import type { HTMLAttributes } from "react";
import { cn } from "../../lib/cn";

type BadgeTone = "neutral" | "positive" | "warning" | "error";

interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  tone?: BadgeTone;
}

const tones: Record<BadgeTone, string> = {
  neutral: "border-terminal-border text-terminal-muted",
  positive: "border-terminal-positive/40 text-terminal-positive",
  warning: "border-terminal-amber/40 text-terminal-amber",
  error: "border-terminal-error/40 text-terminal-error",
};

export function Badge({ className, tone = "neutral", ...props }: BadgeProps) {
  return (
    <span
      className={cn("inline-flex rounded-full border px-2.5 py-1 text-xs font-medium", tones[tone], className)}
      {...props}
    />
  );
}
