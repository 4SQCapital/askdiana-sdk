import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { CHART_COLORS } from "../../const/colors";
import { byFormat } from "../../lib/format";
import type { ChartPoint, ChartType, ValueFormat } from "../../types/dashboard";

const ANIMATE = false;
const TICK = { fontSize: 11, fill: "currentColor" };
const AXIS_WIDTH = 64;
const HBAR_LABEL_WIDTH = 140;
const DONUT_INNER = "55%";
const PIE_OUTER = "80%";
const AREA_FILL_ALPHA = "33";
const GRID_STROKE = "hsl(var(--border))";
const TOOLTIP_STYLE = {
  backgroundColor: "hsl(var(--popover))",
  border: "1px solid hsl(var(--border))",
  borderRadius: 8,
  color: "hsl(var(--popover-foreground))",
  fontSize: 12,
};
// Recharts colours each tooltip row with its series colour, or black when the series has none (bars with per-cell fills)
const TOOLTIP_TEXT = { color: "hsl(var(--popover-foreground))" };

function colorAt(point: ChartPoint, index: number): string {
  return point.color ?? CHART_COLORS.series[index % CHART_COLORS.series.length];
}

function formatters(format?: ValueFormat) {
  if (!format) return { axis: undefined, tooltip: undefined };
  const axisFormat: ValueFormat =
    format === "currency" ? "currency_compact" : format;
  const tipFormat: ValueFormat =
    format === "currency_compact" ? "currency" : format;
  return {
    axis: (v: number) => byFormat(Number(v), axisFormat),
    tooltip: (v: number) => byFormat(Number(v), tipFormat),
  };
}

export function renderChartBody(
  type: ChartType,
  data: ChartPoint[],
  format?: ValueFormat,
) {
  const f = formatters(format);
  const tooltip = (
    <Tooltip
      contentStyle={TOOLTIP_STYLE}
      itemStyle={TOOLTIP_TEXT}
      labelStyle={TOOLTIP_TEXT}
      cursor={{ fill: "hsl(var(--muted))", opacity: 0.4 }}
      formatter={f.tooltip ? (v) => f.tooltip!(Number(v)) : undefined}
    />
  );
  const primary = CHART_COLORS.primary;

  switch (type) {
    case "pie":
    case "donut":
      return (
        <PieChart>
          <Pie
            data={data}
            isAnimationActive={ANIMATE}
            dataKey="value"
            nameKey="label"
            innerRadius={type === "donut" ? DONUT_INNER : 0}
            outerRadius={PIE_OUTER}
            paddingAngle={type === "donut" ? 2 : 0}
            stroke="hsl(var(--card))"
          >
            {data.map((p, i) => (
              <Cell key={i} fill={colorAt(p, i)} />
            ))}
          </Pie>
          {tooltip}
          <Legend wrapperStyle={{ fontSize: 12 }} />
        </PieChart>
      );
    case "line":
      return (
        <LineChart data={data} margin={{ left: 8, right: 16, top: 8 }}>
          <CartesianGrid
            strokeDasharray="3 3"
            vertical={false}
            stroke={GRID_STROKE}
          />
          <XAxis
            dataKey="label"
            tick={TICK}
            tickLine={false}
            axisLine={false}
          />
          <YAxis
            tick={TICK}
            width={AXIS_WIDTH}
            tickFormatter={f.axis}
            tickLine={false}
            axisLine={false}
          />
          {tooltip}
          <Line
            isAnimationActive={ANIMATE}
            type="monotone"
            dataKey="value"
            stroke={primary}
            strokeWidth={2}
            dot={{ r: 3 }}
          />
        </LineChart>
      );
    case "area":
      return (
        <AreaChart data={data} margin={{ left: 8, right: 16, top: 8 }}>
          <CartesianGrid
            strokeDasharray="3 3"
            vertical={false}
            stroke={GRID_STROKE}
          />
          <XAxis
            dataKey="label"
            tick={TICK}
            tickLine={false}
            axisLine={false}
          />
          <YAxis
            tick={TICK}
            width={AXIS_WIDTH}
            tickFormatter={f.axis}
            tickLine={false}
            axisLine={false}
          />
          {tooltip}
          <Area
            isAnimationActive={ANIMATE}
            type="monotone"
            dataKey="value"
            stroke={primary}
            strokeWidth={2}
            fill={`${primary}${AREA_FILL_ALPHA}`}
          />
        </AreaChart>
      );
    case "bar":
      return (
        <BarChart data={data} margin={{ left: 8, right: 16, top: 8 }}>
          <CartesianGrid
            strokeDasharray="3 3"
            vertical={false}
            stroke={GRID_STROKE}
          />
          <XAxis
            dataKey="label"
            tick={TICK}
            interval={0}
            angle={-20}
            textAnchor="end"
            height={54}
            tickLine={false}
          />
          <YAxis
            tick={TICK}
            width={AXIS_WIDTH}
            tickFormatter={f.axis}
            tickLine={false}
            axisLine={false}
          />
          {tooltip}
          <Bar
            isAnimationActive={ANIMATE}
            dataKey="value"
            radius={[6, 6, 0, 0]}
            maxBarSize={48}
          >
            {data.map((p, i) => (
              <Cell key={i} fill={p.color ?? primary} />
            ))}
          </Bar>
        </BarChart>
      );
    case "horizontal_bar":
    default:
      return (
        <BarChart data={data} layout="vertical" margin={{ left: 8, right: 16 }}>
          <XAxis type="number" hide />
          <YAxis
            type="category"
            dataKey="label"
            width={HBAR_LABEL_WIDTH}
            tick={TICK}
            tickLine={false}
            axisLine={false}
          />
          {tooltip}
          <Bar
            isAnimationActive={ANIMATE}
            dataKey="value"
            radius={[0, 6, 6, 0]}
            maxBarSize={24}
          >
            {data.map((p, i) => (
              <Cell key={i} fill={p.color ?? primary} />
            ))}
          </Bar>
        </BarChart>
      );
  }
}
