import { useCallback, useState } from "react";
import { App as ExtShell, bridge, type InitData } from "askdiana-ui";
import { ChartTypeSelect } from "../../components/charts/ChartTypeSelect";
import { ChartView } from "../../components/charts/ChartView";
import { Modal } from "../../components/ui/Modal";
import { useHostEvent } from "../../hooks/useHostEvent";
import { HOST_EVENT, type ModalRequest } from "../../lib/host";
import type { DashboardChart } from "../../types/dashboard";
import { ConnectionDialog } from "../connection/ConnectionDialog";

const close = () => bridge.close();

function ExpandedChart({ chart }: { chart: DashboardChart }) {
  const [type, setType] = useState(chart.type);
  return (
    <Modal
      open
      inline
      title={chart.title}
      onClose={close}
      actions={<ChartTypeSelect value={type} onChange={setType} />}
    >
      <ChartView
        type={type}
        data={chart.data}
        format={chart.value_format}
        expanded
      />
    </Modal>
  );
}

function ConnectionModal({ installId }: { installId: string }) {
  const [refreshKey, setRefreshKey] = useState(0);
  const refresh = useCallback(() => setRefreshKey((k) => k + 1), []);
  useHostEvent(HOST_EVENT.connectionChanged, refresh);
  return (
    <ConnectionDialog
      open
      inline
      onClose={close}
      installId={installId}
      refreshKey={refreshKey}
      onRetry={refresh}
    />
  );
}

export default function ModalView({
  init,
  installId,
}: {
  init: InitData;
  installId: string;
}) {
  const request = init.params as ModalRequest | undefined;
  return (
    <ExtShell bare>
      {request?.modal === "chart" ? (
        <ExpandedChart chart={request.chart} />
      ) : request?.modal === "connection" ? (
        <ConnectionModal installId={installId} />
      ) : (
        <Modal open inline title="Not available" onClose={close}>
          <p className="text-sm text-muted-foreground">
            This dialog could not be opened. Close it and try again.
          </p>
        </Modal>
      )}
    </ExtShell>
  );
}
