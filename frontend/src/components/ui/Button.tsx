import type { ButtonHTMLAttributes } from "react";
import { cn } from "../../lib/cn";

type ButtonVariant = "primary" | "secondary" | "ghost" | "danger";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
}

const variants: Record<ButtonVariant, string> = {
  primary: "bg-terminal-amber text-terminal-bg hover:bg-amber-300",
  secondary: "border border-terminal-border bg-terminal-surface text-terminal-text hover:border-terminal-amber",
  ghost: "text-terminal-muted hover:bg-terminal-surface hover:text-terminal-text",
  danger: "bg-terminal-error text-white hover:bg-red-400",
};

export function Button({ className, variant = "primary", ...props }: ButtonProps) {
  return (
    <button
      className={cn(
        "inline-flex min-h-10 items-center justify-center rounded-md px-4 py-2 text-sm font-semibold transition-colors disabled:cursor-not-allowed disabled:opacity-50",
        variants[variant],
        className,
      )}
      {...props}
    />
  );
}
