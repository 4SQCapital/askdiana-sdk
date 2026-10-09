import { useState } from "react";
import { cn } from "askdiana-ui";
import { ChartGrid } from "../../components/charts/ChartGrid";
import { ErrorState } from "../../components/feedback/ErrorState";
import {
  ChartSkeleton,
  KpiSkeleton,
} from "../../components/feedback/Skeletons";
import { KpiGrid } from "../../components/kpi/KpiGrid";
import { MoneyBar } from "../../components/kpi/MoneyBar";
import { ScrollTabs } from "../../components/navigation/ScrollTabs";
import { useDashboard } from "../../hooks/useErpData";

interface DashboardViewProps {
  installId: string;
  refreshKey: number;
  onRetry: () => void;
}

export function DashboardView({
  installId,
  refreshKey,
  onRetry,
}: DashboardViewProps) {
  const [tabId, setTabId] = useState("");
  const { data, loading, error } = useDashboard(installId, tabId, refreshKey);

  const tab = data?.tab;
  const switchingTab = loading && (!tab || (tabId !== "" && tab.id !== tabId));

  return (
    <div className="space-y-4">
      {data && data.tabs.length > 1 && (
        <ScrollTabs
          tabs={data.tabs}
          activeId={tabId || tab?.id || ""}
          onSelect={setTabId}
          ariaLabel="Dashboard sections"
        />
      )}

      {error && !loading ? (
        <ErrorState message={error} onRetry={onRetry} />
      ) : switchingTab ? (
        <>
          <KpiSkeleton />
          <ChartSkeleton />
        </>
      ) : (
        tab && (
          <div
            className={cn(
              "space-y-4 transition-opacity",
              loading && "opacity-60",
            )}
          >
            {tab.bars?.map((bar) => <MoneyBar key={bar.title} bar={bar} />)}
            <KpiGrid tiles={tab.tiles} />
            <ChartGrid key={tab.id} charts={tab.charts} />
          </div>
        )
      )}
    </div>
  );
}
