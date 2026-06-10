import React, { useEffect, useRef } from "react";
import { ErrorBoundary } from "./ErrorBoundary";
import { bridge } from "../bridge";
import { cn } from "../lib/cn";

export interface ChartContainerProps {
  children: React.ReactNode;
  className?: string;
  /** Width / height ratio, e.g. 16/9. Ignored when `height` is set. */
  aspectRatio?: number;
  /** Fixed height in px. Takes precedence over `aspectRatio`. */
  height?: number;
  /** Report height changes to the host via bridge.resize() — use in App panels and embeds. */
  reportResize?: boolean;
  label?: string;
}

/**
 * Charting-library-agnostic sizing wrapper: gives a chart a predictable box
 * (fixed height or aspect ratio), isolates render errors, and optionally
 * tells the host to resize the iframe/panel as content grows.
 */
export function ChartContainer({
  children,
  className,
  aspectRatio = 16 / 9,
  height,
  reportResize = false,
  label = "This chart could not be displayed.",
}: ChartContainerProps) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!reportResize || !ref.current) return;
    const el = ref.current;
    const observer = new ResizeObserver((entries) => {
      for (const entry of entries) {
        bridge.resize(Math.ceil(entry.contentRect.height));
      }
    });
    observer.observe(el);
    return () => observer.disconnect();
  }, [reportResize]);

  return (
    <ErrorBoundary label={label}>
      <div
        ref={ref}
        className={cn("w-full", className)}
        style={height ? { height } : { aspectRatio }}
      >
        {children}
      </div>
    </ErrorBoundary>
  );
}
