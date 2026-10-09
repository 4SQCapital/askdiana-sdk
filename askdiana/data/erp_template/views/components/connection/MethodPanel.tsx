import type { ReactNode } from "react";
import type { ConnectOption } from "../../types/connection";

interface MethodPanelProps {
  option: ConnectOption;
  current: boolean;
  children: ReactNode;
}

export function MethodPanel({ option, current, children }: MethodPanelProps) {
  return (
    <section className="rounded-xl border bg-background p-4" aria-label={option.label}>
      <div className="flex items-start justify-between gap-2">
        <h3 className="text-sm font-semibold">{option.label}</h3>
        {current && (
          <span className="flex-none rounded-full bg-emerald-100 px-2 py-0.5 text-[11px] font-medium text-emerald-900 dark:bg-emerald-950 dark:text-emerald-100">
            In use
          </span>
        )}
      </div>
      {option.description && (
        <p className="mt-1 text-xs leading-relaxed text-muted-foreground">{option.description}</p>
      )}
      <div className="mt-3">{children}</div>
    </section>
  );
}
