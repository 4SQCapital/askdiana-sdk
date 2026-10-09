import { cn } from "askdiana-ui";
import type { ConnectionPayload } from "../../types/connection";

export function ConnectionSummary({ status }: { status: ConnectionPayload }) {
  return (
    <div
      className={cn(
        "flex items-start gap-3 rounded-lg border p-3",
        status.connected
          ? "border-emerald-200 bg-emerald-50 dark:border-emerald-900 dark:bg-emerald-950/40"
          : "border-amber-200 bg-amber-50 dark:border-amber-900 dark:bg-amber-950/40",
      )}
    >
      <span
        className={cn(
          "mt-1.5 h-2 w-2 flex-none rounded-full",
          status.connected ? "bg-emerald-500" : "bg-amber-500",
        )}
      />
      <div className="min-w-0 text-sm">
        {status.connected ? (
          <>
            <p className="font-medium">Connected{status.account ? ` to ${status.account}` : ""}</p>
            {status.method_label && (
              <p className="text-xs text-muted-foreground">Using {status.method_label}</p>
            )}
          </>
        ) : (
          <>
            <p className="font-medium">Not connected</p>
            <p className="text-xs text-muted-foreground">
              The dashboard shows sample data until you connect {status.label}.
            </p>
          </>
        )}
      </div>
    </div>
  );
}
