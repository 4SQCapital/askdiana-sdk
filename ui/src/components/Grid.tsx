import React from "react";
import { cn } from "../lib/cn";

export interface GridProps extends React.HTMLAttributes<HTMLDivElement> {
  columns?: number;
  /** Gap, in multiples of 0.25rem (Tailwind spacing scale). */
  gap?: number;
}

export function Grid({ columns = 2, gap = 3, className, style, ...props }: GridProps) {
  return (
    <div
      className={cn("grid", className)}
      style={{
        gridTemplateColumns: `repeat(${columns}, minmax(0, 1fr))`,
        gap: `${gap * 0.25}rem`,
        ...style,
      }}
      {...props}
    />
  );
}
