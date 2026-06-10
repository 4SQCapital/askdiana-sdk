import { useEffect, useState } from "react";

export interface ChartColors {
  /** Ordered palette for series/categories — plain hsl()/hex strings. */
  palette: string[];
  grid: string;
  axis: string;
  tooltipBg: string;
  tooltipFg: string;
  tooltipBorder: string;
}

const PALETTE_VARS = [
  "--primary",
  "--secondary",
  "--accent",
  "--muted-foreground",
  "--destructive",
  "--ring",
] as const;

function readVar(name: string, fallback: string) {
  if (typeof window === "undefined") return fallback;
  const value = getComputedStyle(document.documentElement)
    .getPropertyValue(name)
    .trim();
  return value ? `hsl(${value})` : fallback;
}

function readColors(): ChartColors {
  return {
    palette: PALETTE_VARS.map((name) => readVar(name, "#8884d8")),
    grid: readVar("--border", "#e2e8f0"),
    axis: readVar("--muted-foreground", "#64748b"),
    tooltipBg: readVar("--popover", "#ffffff"),
    tooltipFg: readVar("--popover-foreground", "#1a1a2e"),
    tooltipBorder: readVar("--border", "#e2e8f0"),
  };
}

/**
 * Reads the host theme's CSS custom properties (defined in `theme.css`) and
 * returns plain `hsl()`/hex color strings — works with recharts, visx, chart.js,
 * or any other charting library an extension chooses. Re-reads automatically
 * when `.dark`/`.light` is toggled on `<html>` so charts follow theme changes.
 */
export function useChartColors(): ChartColors {
  const [colors, setColors] = useState<ChartColors>(() => readColors());

  useEffect(() => {
    setColors(readColors());
    const root = document.documentElement;
    const observer = new MutationObserver(() => setColors(readColors()));
    observer.observe(root, { attributes: true, attributeFilter: ["class"] });
    return () => observer.disconnect();
  }, []);

  return colors;
}
