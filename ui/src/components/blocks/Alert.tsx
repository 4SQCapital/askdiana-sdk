import React from "react";
import { cn } from "../../lib/cn";

const variants: Record<string, string> = {
  info: "bg-blue-50 text-blue-900 dark:bg-blue-950 dark:text-blue-100",
  success:
    "bg-emerald-50 text-emerald-900 dark:bg-emerald-950 dark:text-emerald-100",
  warning: "bg-amber-50 text-amber-900 dark:bg-amber-950 dark:text-amber-100",
  error: "bg-red-50 text-red-900 dark:bg-red-950 dark:text-red-100",
};

interface AlertProps {
  children?: React.ReactNode;
  content?: string;
  variant?: keyof typeof variants;
}

export function Alert({ children, content, variant = "info" }: AlertProps) {
  return (
    <div
      className={cn(
        "rounded-md px-3 py-2 text-sm",
        variants[variant] ?? variants.info,
      )}
    >
      {content ?? children}
    </div>
  );
}
