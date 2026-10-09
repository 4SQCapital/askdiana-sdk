import { cn } from "askdiana-ui";
import { SortIcon } from "../ui/icons";

export type SortDirection = "asc" | "desc";

export interface GridColumn {
  key: string;
  header: string;
  align?: "left" | "right";
}

export interface GridSort {
  key: string;
  direction: SortDirection;
}

interface DataGridProps {
  columns: GridColumn[];
  rows: string[][];
  rowKey?: (index: number) => string | number;
  sort?: GridSort | null;
  onSort?: (key: string) => void;
}

export function DataGrid({
  columns,
  rows,
  rowKey = (i) => i,
  sort,
  onSort,
}: DataGridProps) {
  return (
    <div className="overflow-auto rounded-lg border">
      <table className="w-full border-collapse text-sm">
        <thead className="sticky top-0 z-[1] bg-muted/80 backdrop-blur">
          <tr>
            {columns.map((col) => {
              const direction = sort?.key === col.key ? sort.direction : null;
              const content = (
                <span
                  className={cn(
                    "inline-flex items-center gap-1",
                    col.align === "right" && "flex-row-reverse",
                  )}
                >
                  {col.header}
                  {onSort && (
                    <SortIcon
                      sortDirection={direction}
                      className={direction ? "text-foreground" : "opacity-40"}
                    />
                  )}
                </span>
              );
              return (
                <th
                  key={col.key}
                  scope="col"
                  aria-sort={
                    direction === "asc"
                      ? "ascending"
                      : direction === "desc"
                        ? "descending"
                        : undefined
                  }
                  className={cn(
                    "whitespace-nowrap border-b px-3 py-2 text-xs font-medium uppercase tracking-wide text-muted-foreground",
                    col.align === "right" ? "text-right" : "text-left",
                  )}
                >
                  {onSort ? (
                    <button
                      type="button"
                      onClick={() => onSort(col.key)}
                      className="uppercase hover:text-foreground"
                    >
                      {content}
                    </button>
                  ) : (
                    content
                  )}
                </th>
              );
            })}
          </tr>
        </thead>
        <tbody>
          {rows.map((cells, i) => (
            <tr
              key={rowKey(i)}
              className="border-b last:border-b-0 hover:bg-muted/40"
            >
              {cells.map((cell, j) => (
                <td
                  key={columns[j]?.key ?? j}
                  className={cn(
                    "whitespace-nowrap px-3 py-2",
                    columns[j]?.align === "right" &&
                      "text-right font-mono tabular-nums",
                  )}
                >
                  {cell}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
