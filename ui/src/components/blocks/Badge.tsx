import React from "react";
import { cn } from "../../lib/cn";

const VARIANTS = {
  default: "bg-primary text-primary-foreground",
  secondary: "bg-secondary text-secondary-foreground",
  outline: "border border-border text-foreground",
  success:
    "bg-emerald-100 text-emerald-900 dark:bg-emerald-950 dark:text-emerald-100",
  warning:
    "bg-amber-100 text-amber-900 dark:bg-amber-950 dark:text-amber-100",
  error: "bg-red-100 text-red-900 dark:bg-red-950 dark:text-red-100",
  info: "bg-blue-100 text-blue-900 dark:bg-blue-950 dark:text-blue-100",
} as const;

export interface BadgeProps {
  children?: React.ReactNode;
  content?: string;
  variant?: keyof typeof VARIANTS;
}

export function Badge({ children, content, variant = "default" }: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium",
        VARIANTS[variant] ?? VARIANTS.default,
      )}
    >
      {content ?? children}
    </span>
  );
}
