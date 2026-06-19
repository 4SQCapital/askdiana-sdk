import React from "react";
import { cn } from "../../lib/cn";

export interface ProgressProps {
  label?: string;
  value: number;
  max?: number;
  variant?: "default" | "success" | "warning" | "error";
}

const VARIANT_BAR = {
  default: "bg-primary",
  success: "bg-emerald-500",
  warning: "bg-amber-500",
  error: "bg-destructive",
} as const;

export function Progress({ label, value, max = 100, variant = "default" }: ProgressProps) {
  const pct = Math.min(100, Math.max(0, (value / max) * 100));
  return (
    <div className="w-full">
      {label && (
        <div className="mb-1 flex items-center justify-between text-xs text-muted-foreground">
          <span>{label}</span>
          <span>{Math.round(pct)}%</span>
        </div>
      )}
      <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
        <div
          className={cn(
            "h-full rounded-full transition-all",
            VARIANT_BAR[variant] ?? VARIANT_BAR.default,
          )}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}
