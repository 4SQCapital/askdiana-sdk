import { Select } from "askdiana-ui";
import type { ChartType } from "../../types/dashboard";
import { CHART_TYPE_OPTIONS, isChartType } from "./chartTypes";

interface ChartTypeSelectProps {
  value: ChartType;
  onChange: (type: ChartType) => void;
}

export function ChartTypeSelect({ value, onChange }: ChartTypeSelectProps) {
  return (
    <Select
      value={value}
      onValueChange={(v) => isChartType(v) && onChange(v)}
      options={CHART_TYPE_OPTIONS}
      className="h-8 w-[140px] text-xs"
    />
  );
}
