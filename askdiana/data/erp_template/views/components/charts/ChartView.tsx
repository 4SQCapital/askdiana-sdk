import { ResponsiveContainer } from "recharts";
import { ChartContainer } from "askdiana-ui";
import type { ChartPoint, ChartType, ValueFormat } from "../../types/dashboard";
import { renderChartBody } from "./ChartBody";
import { chartHeight, DEFAULT_CHART_TYPE } from "./chartTypes";

interface ChartViewProps {
  type?: ChartType;
  data: ChartPoint[];
  format?: ValueFormat;
  expanded?: boolean;
}

export function ChartView({
  type = DEFAULT_CHART_TYPE,
  data,
  format,
  expanded = false,
}: ChartViewProps) {
  const points = data.filter((d) => d && typeof d.value === "number");
  if (!points.length) {
    return (
      <p className="py-8 text-center text-xs text-muted-foreground">
        No data for this chart yet.
      </p>
    );
  }
  return (
    <ChartContainer height={chartHeight(type, points.length, expanded)}>
      <ResponsiveContainer width="100%" height="100%">
        {renderChartBody(type, points, format)}
      </ResponsiveContainer>
    </ChartContainer>
  );
}
