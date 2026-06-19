import React from "react";
import { cn } from "../../lib/cn";

export interface TimelineStep {
  title: string;
  description?: string;
  timestamp?: string;
  status?: "complete" | "current" | "upcoming";
}

export interface TimelineProps {
  items: TimelineStep[];
}

const DOT_VARIANTS = {
  complete: "bg-primary border-primary",
  current: "bg-background border-primary",
  upcoming: "bg-background border-border",
} as const;

export function Timeline({ items }: TimelineProps) {
  return (
    <ol className="relative space-y-4 border-l border-border pl-4">
      {items.map((item, i) => (
        <li key={i} className="relative">
          <span
            className={cn(
              "absolute -left-[1.3125rem] top-1 h-2.5 w-2.5 rounded-full border-2",
              DOT_VARIANTS[item.status ?? "upcoming"],
            )}
          />
          <div className="flex items-baseline justify-between gap-2">
            <span className="text-sm font-medium text-foreground">{item.title}</span>
            {item.timestamp && (
              <span className="text-xs text-muted-foreground">{item.timestamp}</span>
            )}
          </div>
          {item.description && (
            <p className="mt-0.5 text-xs text-muted-foreground">{item.description}</p>
          )}
        </li>
      ))}
    </ol>
  );
}
