import { cn } from "askdiana-ui";
import type { Mode } from "../../types/dashboard";

const MODE_STYLE: Record<
  Mode,
  { text: string; className: string; dot: string }
> = {
  live: {
    text: "Live",
    className:
      "bg-emerald-100 text-emerald-900 dark:bg-emerald-950 dark:text-emerald-100",
    dot: "bg-emerald-500",
  },
  demo: {
    text: "Sample data",
    className: "bg-blue-100 text-blue-900 dark:bg-blue-950 dark:text-blue-100",
    dot: "bg-blue-500",
  },
  disconnected: {
    text: "Not connected",
    className:
      "bg-amber-100 text-amber-900 dark:bg-amber-950 dark:text-amber-100",
    dot: "bg-amber-500",
  },
};

export function StatusBadge({ mode }: { mode: Mode }) {
  const style = MODE_STYLE[mode];
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full px-2 py-0.5 text-xs font-medium",
        style.className,
      )}
    >
      <span
        className={cn(
          "h-1.5 w-1.5 rounded-full",
          style.dot,
          mode === "live" && "animate-pulse",
        )}
      />
      {style.text}
    </span>
  );
}
