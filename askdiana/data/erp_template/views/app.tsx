import { useEffect, useState } from "react";
import { App as ExtShell, Button, type InitData } from "askdiana-ui";
import { Banner } from "./components/feedback/Banner";
import { PanelHeader } from "./components/layout/PanelHeader";
import {
  ChartIcon,
  PlugIcon,
  RefreshIcon,
  TableIcon,
} from "./components/ui/icons";
import { IconButton } from "./components/ui/IconButton";
import {
  SegmentedControl,
  type SegmentOption,
} from "./components/ui/SegmentedControl";
import { StatusBadge } from "./components/ui/StatusBadge";
import { DashboardView } from "./features/dashboard/DashboardView";
import { ConnectionDialog } from "./features/connection/ConnectionDialog";
import { DataView } from "./features/data/DataView";
import { useMeta } from "./hooks/useErpData";
import { useHostEvent } from "./hooks/useHostEvent";
import { HOST_EVENT, IN_HOST, openHostModal } from "./lib/host";
import { setCurrency } from "./lib/format";
import type { Mode } from "./types/dashboard";

type View = "dashboard" | "data";

const VIEWS: SegmentOption<View>[] = [
  {
    value: "dashboard",
    label: "Dashboard",
    icon: <ChartIcon width={14} height={14} />,
  },
  { value: "data", label: "Data", icon: <TableIcon width={14} height={14} /> },
];

function initialView(): View {
  return new URLSearchParams(location.search).get("panel") === "data"
    ? "data"
    : "dashboard";
}

const MODE_HINT: Partial<Record<Mode, string>> = {
  demo: "You're looking at sample data. Connect your account to see your own.",
  disconnected: "Not connected. Connect your account to see your data.",
};

export default function DashboardApp({
  installId,
}: {
  init: InitData;
  installId: string;
}) {
  const [view, setView] = useState<View>(initialView);
  const [refreshKey, setRefreshKey] = useState(0);
  const refresh = () => setRefreshKey((k) => k + 1);
  const [connectionOpen, setConnectionOpen] = useState(false);
  const openConnection = () =>
    IN_HOST
      ? openHostModal({ modal: "connection", size: "md" })
      : setConnectionOpen(true);
  useHostEvent(HOST_EVENT.connectionChanged, refresh);
  const meta = useMeta(installId, refreshKey);

  useEffect(() => setCurrency(meta.data?.currency), [meta.data?.currency]);

  const mode = meta.data?.mode;
  const hint = mode ? MODE_HINT[mode] : undefined;

  return (
    <ExtShell bare>
      <div className="erp-app flex min-h-full flex-col">
        <PanelHeader
          title={meta.data?.label ?? "Dashboard"}
          subtitle={
            view === "dashboard" ? "Key figures and charts" : "Raw records"
          }
          badge={mode && <StatusBadge mode={mode} />}
          actions={
            <>
              <SegmentedControl
                options={VIEWS}
                value={view}
                onChange={setView}
                ariaLabel="View"
              />
              <IconButton
                label="Connection"
                onClick={openConnection}
                disabled={!installId}
              >
                <PlugIcon />
              </IconButton>
              <IconButton
                label="Refresh"
                onClick={refresh}
                spinning={meta.loading}
              >
                <RefreshIcon />
              </IconButton>
            </>
          }
        />
        <main className="flex-1 space-y-4 p-4">
          {hint && (
            <Banner
              tone={mode === "demo" ? "info" : "warning"}
              action={
                <Button size="sm" variant="outline" onClick={openConnection}>
                  Connect
                </Button>
              }
            >
              {hint}
            </Banner>
          )}
          {!installId ? (
            <Banner tone="warning">
              Open this panel from AskDiana, or add ?install_id=demo to the
              address to preview it.
            </Banner>
          ) : view === "dashboard" ? (
            <DashboardView
              installId={installId}
              refreshKey={refreshKey}
              onRetry={refresh}
            />
          ) : (
            <DataView
              installId={installId}
              entities={meta.data?.entities ?? []}
              refreshKey={refreshKey}
              onRetry={refresh}
            />
          )}
        </main>
      </div>
      <ConnectionDialog
        open={connectionOpen}
        onClose={() => setConnectionOpen(false)}
        installId={installId}
        refreshKey={refreshKey}
        onRetry={refresh}
      />
    </ExtShell>
  );
}
