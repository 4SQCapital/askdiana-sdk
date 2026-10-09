import type { ChartType } from "../../types/dashboard";

export const DEFAULT_CHART_TYPE: ChartType = "horizontal_bar";

export const CHART_TYPE_OPTIONS: { value: ChartType; label: string }[] = [
  { value: "horizontal_bar", label: "Horizontal bar" },
  { value: "bar", label: "Bar" },
  { value: "line", label: "Line" },
  { value: "area", label: "Area" },
  { value: "donut", label: "Donut" },
  { value: "pie", label: "Pie" },
];

const HBAR_ROW_HEIGHT = 36;
const HBAR_MIN_HEIGHT = 180;
const CHART_HEIGHT = 260;
const EXPANDED_HEIGHT = 480;

export function chartHeight(
  type: ChartType,
  points: number,
  expanded = false,
): number {
  if (type === "horizontal_bar") {
    const natural = Math.max(HBAR_MIN_HEIGHT, points * HBAR_ROW_HEIGHT);
    return expanded ? Math.max(natural, EXPANDED_HEIGHT) : natural;
  }
  return expanded ? EXPANDED_HEIGHT : CHART_HEIGHT;
}

export function isChartType(value: string | undefined): value is ChartType {
  return CHART_TYPE_OPTIONS.some((o) => o.value === value);
}
