import React from "react";
import { cn } from "../../lib/cn";

interface ListProps {
  items?: React.ReactNode[];
  ordered?: boolean;
}

export function List({ items = [], ordered }: ListProps) {
  const cls = "ml-5 space-y-1 text-sm text-foreground";
  const lis = items.map((it, i) => <li key={i}>{it}</li>);
  return ordered ? (
    <ol className={cn(cls, "list-decimal")}>{lis}</ol>
  ) : (
    <ul className={cn(cls, "list-disc")}>{lis}</ul>
  );
}
