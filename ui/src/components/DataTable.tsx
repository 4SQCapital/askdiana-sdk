import React, { useMemo, useState } from "react";
import { ArrowDown, ArrowUp, ArrowUpDown } from "lucide-react";
import { cn } from "../lib/cn";

export interface DataTableColumn<T> {
  key: keyof T & string;
  header: string;
  align?: "left" | "right" | "center";
  render?: (row: T) => React.ReactNode;
  sortable?: boolean;
}

export interface DataTableProps<T> {
  columns: DataTableColumn<T>[];
  data: T[];
  className?: string;
}

const ALIGN_MAP = {
  left: "text-left",
  right: "text-right",
  center: "text-center",
} as const;

export function DataTable<T extends object>({
  columns,
  data,
  className,
}: DataTableProps<T>) {
  const [sort, setSort] = useState<{ key: string; dir: "asc" | "desc" } | null>(null);

  const rows = useMemo(() => {
    if (!sort) return data;
    const { key, dir } = sort;
    const k = key as keyof T;
    return [...data].sort((a, b) => {
      const av = a[k];
      const bv = b[k];
      if (av == null || bv == null) return 0;
      if (typeof av === "number" && typeof bv === "number") {
        return dir === "asc" ? av - bv : bv - av;
      }
      return dir === "asc"
        ? String(av).localeCompare(String(bv))
        : String(bv).localeCompare(String(av));
    });
  }, [data, sort]);

  function toggleSort(key: string) {
    setSort((s) => {
      if (!s || s.key !== key) return { key, dir: "asc" };
      if (s.dir === "asc") return { key, dir: "desc" };
      return null;
    });
  }

  return (
    <div className={cn("overflow-x-auto rounded-md border border-border", className)}>
      <table className="w-full text-sm">
        <thead>
          <tr className="bg-muted/50">
            {columns.map((col) => (
              <th
                key={col.key}
                className={cn(
                  "border-b border-border px-3 py-2 font-medium text-muted-foreground",
                  ALIGN_MAP[col.align ?? "left"],
                  col.sortable && "cursor-pointer select-none hover:text-foreground",
                )}
                onClick={col.sortable ? () => toggleSort(col.key) : undefined}
              >
                <span className="inline-flex items-center gap-1">
                  {col.header}
                  {col.sortable &&
                    (sort?.key === col.key ? (
                      sort.dir === "asc" ? (
                        <ArrowUp className="h-3 w-3" />
                      ) : (
                        <ArrowDown className="h-3 w-3" />
                      )
                    ) : (
                      <ArrowUpDown className="h-3 w-3 opacity-40" />
                    ))}
                </span>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, ri) => (
            <tr key={ri} className="border-b border-border/50 last:border-0">
              {columns.map((col) => (
                <td key={col.key} className={cn("px-3 py-2", ALIGN_MAP[col.align ?? "left"])}>
                  {col.render ? col.render(row) : String(row[col.key] ?? "")}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
