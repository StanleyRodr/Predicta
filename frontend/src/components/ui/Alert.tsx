import type { HTMLAttributes } from "react";
import { cn } from "../../lib/cn";

type AlertTone = "info" | "success" | "error";

interface AlertProps extends HTMLAttributes<HTMLDivElement> {
  tone?: AlertTone;
}

const tones: Record<AlertTone, string> = {
  info: "border-terminal-border text-terminal-muted",
  success: "border-terminal-positive/50 text-terminal-positive",
  error: "border-terminal-error/50 text-terminal-error",
};

export function Alert({ className, tone = "info", ...props }: AlertProps) {
  return (
    <div
      role={tone === "error" ? "alert" : "status"}
      className={cn("rounded-md border bg-terminal-bg p-3 text-sm", tones[tone], className)}
      {...props}
    />
  );
}
