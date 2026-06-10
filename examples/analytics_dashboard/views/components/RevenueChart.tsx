import React from "react";
import {
  Area,
  CartesianGrid,
  ComposedChart,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { ChartContainer, useChartColors } from "askdiana-ui";
import { revenueSeries } from "../data/mock";

export interface RevenueChartProps {
  /** Tell the host to resize the iframe/panel as the chart's box grows. */
  reportResize?: boolean;
}

export function RevenueChart({ reportResize }: RevenueChartProps) {
  const colors = useChartColors();

  return (
    <ChartContainer aspectRatio={16 / 7} reportResize={reportResize}>
      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart data={revenueSeries} margin={{ top: 8, right: 12, left: -16, bottom: 0 }}>
          <CartesianGrid stroke={colors.grid} strokeDasharray="3 3" vertical={false} />
          <XAxis
            dataKey="month"
            stroke={colors.axis}
            fontSize={12}
            tickLine={false}
            axisLine={false}
          />
          <YAxis
            yAxisId="revenue"
            stroke={colors.axis}
            fontSize={12}
            tickLine={false}
            axisLine={false}
            tickFormatter={(v: number) => `$${Math.round(v / 1000)}k`}
          />
          <YAxis yAxisId="orders" orientation="right" hide />
          <Tooltip
            contentStyle={{
              background: colors.tooltipBg,
              color: colors.tooltipFg,
              border: `1px solid ${colors.tooltipBorder}`,
              borderRadius: 8,
              fontSize: 12,
            }}
          />
          <Area
            yAxisId="revenue"
            type="monotone"
            dataKey="revenue"
            name="Revenue"
            stroke={colors.palette[0]}
            fill={colors.palette[0]}
            fillOpacity={0.15}
            strokeWidth={2}
          />
          <Line
            yAxisId="orders"
            type="monotone"
            dataKey="orders"
            name="Orders"
            stroke={colors.palette[1]}
            strokeWidth={2}
            dot={false}
          />
        </ComposedChart>
      </ResponsiveContainer>
    </ChartContainer>
  );
}
