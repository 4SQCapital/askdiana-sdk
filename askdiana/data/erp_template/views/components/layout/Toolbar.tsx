import type { ReactNode } from "react";

/** A card-style bar for filters and actions: `start` grows, `end` stays on the right. */
export function Toolbar({
  start,
  end,
}: {
  start?: ReactNode;
  end?: ReactNode;
}) {
  return (
    <div className="flex flex-wrap items-center gap-2 rounded-lg border bg-card p-2">
      <div className="flex min-w-0 flex-1 flex-wrap items-center gap-2">
        {start}
      </div>
      {end && <div className="flex items-center gap-2">{end}</div>}
    </div>
  );
}
