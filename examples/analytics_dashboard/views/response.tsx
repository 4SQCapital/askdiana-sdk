import React from "react";
import { Response, Stat, Grid, Embed, type InitData } from "askdiana-ui";
import { kpis } from "./data/mock";

/**
 * Chat (Response) surface: a compact KPI summary plus an `embed` pointing at
 * `?view=chart`, which renders the full RevenueChart inline (see chart.tsx).
 */
export default function AnalyticsResponse({ init }: { init: InitData; installId: string }) {
  const serverBlocks = init.params?.blocks as any[] | undefined;
  if (serverBlocks) return <Response blocks={serverBlocks} />;

  const chartUrl = `${location.origin}${location.pathname}?view=chart`;

  return (
    <Response>
      <div className="space-y-4 p-2">
        <div>
          <h3 className="mb-2 text-sm font-semibold text-foreground">Key metrics</h3>
          <Grid columns={2} gap={2}>
            <Stat label={kpis.revenue.label} value={kpis.revenue.value} delta={kpis.revenue.delta} trend={kpis.revenue.trend} />
            <Stat label={kpis.activeUsers.label} value={kpis.activeUsers.value} delta={kpis.activeUsers.delta} trend={kpis.activeUsers.trend} />
            <Stat label={kpis.conversionRate.label} value={kpis.conversionRate.value} delta={kpis.conversionRate.delta} trend={kpis.conversionRate.trend} />
            <Stat label={kpis.avgOrderValue.label} value={kpis.avgOrderValue.value} delta={kpis.avgOrderValue.delta} trend={kpis.avgOrderValue.trend} />
          </Grid>
        </div>

        <Embed url={chartUrl} title="Revenue trend" aspectRatio="16:9" />
      </div>
    </Response>
  );
}
