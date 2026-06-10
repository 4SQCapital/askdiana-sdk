import React from "react";
import { cn } from "../lib/cn";

export interface StackProps extends React.HTMLAttributes<HTMLDivElement> {
  direction?: "row" | "column";
  /** Gap, in multiples of 0.25rem (Tailwind spacing scale). */
  gap?: number;
  align?: "start" | "center" | "end" | "stretch";
  justify?: "start" | "center" | "end" | "between";
  wrap?: boolean;
}

const ALIGN_MAP = {
  start: "items-start",
  center: "items-center",
  end: "items-end",
  stretch: "items-stretch",
} as const;

const JUSTIFY_MAP = {
  start: "justify-start",
  center: "justify-center",
  end: "justify-end",
  between: "justify-between",
} as const;

export function Stack({
  direction = "column",
  gap = 2,
  align,
  justify,
  wrap,
  className,
  style,
  ...props
}: StackProps) {
  return (
    <div
      className={cn(
        "flex",
        direction === "row" ? "flex-row" : "flex-col",
        align && ALIGN_MAP[align],
        justify && JUSTIFY_MAP[justify],
        wrap && "flex-wrap",
        className,
      )}
      style={{ gap: `${gap * 0.25}rem`, ...style }}
      {...props}
    />
  );
}
