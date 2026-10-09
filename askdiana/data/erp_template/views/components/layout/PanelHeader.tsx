import type { ReactNode } from "react";
import { BRAND_COLOR } from "../../const/colors";

interface PanelHeaderProps {
  title: string;
  subtitle?: string;
  badge?: ReactNode;
  actions?: ReactNode;
}

export function PanelHeader({
  title,
  subtitle,
  badge,
  actions,
}: PanelHeaderProps) {
  return (
    <header className="erp-header flex flex-wrap items-center justify-between gap-3 border-b px-4 py-3">
      <div className="flex min-w-0 items-center gap-3">
        <div
          className="erp-brand-mark flex h-9 w-9 shrink-0 items-center justify-center rounded-lg text-sm font-bold text-white shadow-sm"
          style={{ backgroundColor: BRAND_COLOR }}
          aria-hidden="true"
        >
          {title.charAt(0).toUpperCase()}
        </div>
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <h1 className="truncate text-base font-semibold leading-tight">
              {title}
            </h1>
            {badge}
          </div>
          {subtitle && (
            <p className="truncate text-xs text-muted-foreground">{subtitle}</p>
          )}
        </div>
      </div>
      {actions && <div className="flex items-center gap-2">{actions}</div>}
    </header>
  );
}
