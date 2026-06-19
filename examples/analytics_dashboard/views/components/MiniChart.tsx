import React, { useMemo } from "react";
import { Area, AreaChart, ResponsiveContainer } from "recharts";
import { useChartColors } from "askdiana-ui";

export interface MiniChartProps {
  data: number[];
  color?: string;
}

/** Tiny sparkline for KPI <Stat> cards — no axes, grid, or tooltip. */
export function MiniChart({ data, color }: MiniChartProps) {
  const colors = useChartColors();
  const series = useMemo(() => data.map((value, i) => ({ i, value })), [data]);
  const stroke = color ?? colors.palette[0];

  return (
    <div className="h-10 w-20">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={series} margin={{ top: 4, right: 0, left: 0, bottom: 0 }}>
          <Area
            type="monotone"
            dataKey="value"
            stroke={stroke}
            fill={stroke}
            fillOpacity={0.15}
            strokeWidth={1.5}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
