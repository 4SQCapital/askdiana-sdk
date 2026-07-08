import React from "react";
import { ArrowDown, ArrowUp, Minus } from "lucide-react";
import { cn } from "../../lib/cn";

export interface StatProps {
  label: string;
  value: string | number;
  delta?: string | number;
  trend?: "up" | "down" | "flat";
  /** Border/background tint -- use to flag at-risk or critical figures. */
  variant?: "default" | "success" | "warning" | "danger";
  children?: React.ReactNode;
}

const TREND_CONFIG = {
  up: { Icon: ArrowUp, className: "text-emerald-600 dark:text-emerald-400" },
  down: { Icon: ArrowDown, className: "text-red-600 dark:text-red-400" },
  flat: { Icon: Minus, className: "text-muted-foreground" },
} as const;

// Solid left-border accent instead of a translucent background wash --
// a wash tuned for light mode goes muddy/indistinguishable over the near-
// black dark background, while a saturated accent border reads clearly in
// both themes without separate tuning.
const VARIANT_CLASS = {
  default: "border-border",
  success: "border-border border-l-4 border-l-emerald-500",
  warning: "border-border border-l-4 border-l-amber-500",
  danger: "border-border border-l-4 border-l-red-500",
} as const;

export function Stat({ label, value, delta, trend, variant = "default", children }: StatProps) {
  const trendConfig = trend ? TREND_CONFIG[trend] : undefined;
  return (
    <div className={cn("rounded-md border bg-card p-3 text-card-foreground", VARIANT_CLASS[variant])}>
      <div className="text-xs text-muted-foreground">{label}</div>
      <div className="mt-1 text-2xl font-semibold tabular-nums">{value}</div>
      {(delta !== undefined || children) && (
        <div className="mt-1 flex items-center gap-1 text-xs">
          {trendConfig && (
            <trendConfig.Icon className={cn("h-3 w-3", trendConfig.className)} />
          )}
          {delta !== undefined && (
            <span className={cn(trendConfig?.className ?? "text-muted-foreground")}>
              {delta}
            </span>
          )}
          {children}
        </div>
      )}
    </div>
  );
}
