import type { SegmentBar } from "../../types/dashboard";

// Each segment gets at least this share of the width, so a small amount stays visible and clickable
const MIN_SHARE = 0.12;
const FALLBACK_COLORS = ["#f97316", "#94a3b8", "#22c55e", "#0ea5e9"];

/** Parts of a whole side by side: big amount and label above a thick coloured bar per segment. */
export function MoneyBar({ bar }: { bar: SegmentBar }) {
  const total = bar.segments.reduce((sum, s) => sum + Math.max(s.amount, 0), 0);
  const raw = bar.segments.map((s) => (total > 0 ? Math.max(s.amount, 0) / total : 1 / bar.segments.length));
  const widened = raw.map((share) => Math.max(share, MIN_SHARE));
  const scale = widened.reduce((a, b) => a + b, 0);

  return (
    <section className="erp-money-bar rounded-xl border bg-card p-4 text-card-foreground shadow-sm" aria-label={bar.title}>
      <div className="mb-3 flex items-baseline justify-between gap-2">
        <h3 className="text-sm font-semibold">{bar.title}</h3>
        <span className="text-xs text-muted-foreground tabular-nums">{bar.total} total</span>
      </div>
      <div className="flex gap-1">
        {bar.segments.map((segment, i) => (
          <div key={segment.label} className="min-w-0" style={{ flexGrow: widened[i] / scale, flexBasis: 0 }}>
            <div className="truncate text-lg font-semibold tabular-nums leading-tight">{segment.value}</div>
            <div className="erp-money-bar-label mb-1.5 truncate text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
              {segment.label}
            </div>
            <div
              className="erp-money-bar-fill h-3 rounded-sm"
              style={{ backgroundColor: segment.color ?? FALLBACK_COLORS[i % FALLBACK_COLORS.length] }}
              title={`${segment.label}: ${segment.value}`}
            />
          </div>
        ))}
      </div>
    </section>
  );
}
