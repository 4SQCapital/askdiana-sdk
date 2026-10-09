import { Skeleton } from "askdiana-ui";

const KPI_PLACEHOLDERS = 4;
const CHART_PLACEHOLDERS = 2;
const TABLE_ROWS = 8;

export function KpiSkeleton({ count = KPI_PLACEHOLDERS }: { count?: number }) {
  return (
    <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
      {Array.from({ length: count }, (_, i) => (
        <div key={i} className="space-y-2 rounded-md border bg-card p-3">
          <Skeleton className="h-3 w-20" />
          <Skeleton className="h-7 w-28" />
          <Skeleton className="h-3 w-14" />
        </div>
      ))}
    </div>
  );
}

export function ChartSkeleton({
  count = CHART_PLACEHOLDERS,
}: {
  count?: number;
}) {
  return (
    <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
      {Array.from({ length: count }, (_, i) => (
        <div key={i} className="space-y-3 rounded-xl border bg-card p-4">
          <Skeleton className="h-4 w-40" />
          <Skeleton className="h-52" />
        </div>
      ))}
    </div>
  );
}

export function TableSkeleton({ rows = TABLE_ROWS }: { rows?: number }) {
  return (
    <div className="space-y-2 rounded-xl border bg-card p-3">
      <Skeleton className="h-6" />
      {Array.from({ length: rows }, (_, i) => (
        <Skeleton key={i} className="h-5" />
      ))}
    </div>
  );
}
