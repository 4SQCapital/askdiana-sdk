import React from "react";
import { Cell, Legend, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";
import { ChartContainer, useChartColors } from "askdiana-ui";
import { categoryBreakdown } from "../data/mock";

export interface CategoryChartProps {
  reportResize?: boolean;
}

export function CategoryChart({ reportResize }: CategoryChartProps) {
  const colors = useChartColors();
  const palette = [...colors.palette, colors.axis, colors.grid];

  return (
    <ChartContainer aspectRatio={4 / 3} reportResize={reportResize}>
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={categoryBreakdown}
            dataKey="value"
            nameKey="name"
            innerRadius="55%"
            outerRadius="85%"
            paddingAngle={2}
          >
            {categoryBreakdown.map((_, i) => (
              <Cell key={i} fill={palette[i % palette.length]} stroke="none" />
            ))}
          </Pie>
          <Tooltip
            contentStyle={{
              background: colors.tooltipBg,
              color: colors.tooltipFg,
              border: `1px solid ${colors.tooltipBorder}`,
              borderRadius: 8,
              fontSize: 12,
            }}
          />
          <Legend wrapperStyle={{ fontSize: 12, color: colors.axis }} />
        </PieChart>
      </ResponsiveContainer>
    </ChartContainer>
  );
}
