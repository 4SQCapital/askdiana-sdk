import { useEffect, useMemo, useState } from "react";
import type { GridColumn, GridSort } from "../../components/table/DataGrid";
import { formatCell, humanize, isNumericType } from "../../lib/format";
import type { EntityRef, RecordRow } from "../../types/dashboard";

function compare(a: unknown, b: unknown): number {
  if (a === b) return 0;
  if (a === null || a === undefined || a === "") return 1;
  if (b === null || b === undefined || b === "") return -1;
  if (typeof a === "number" && typeof b === "number") return a - b;
  return String(a).localeCompare(String(b), undefined, {
    numeric: true,
    sensitivity: "base",
  });
}

export function useRecordTable(
  entity: EntityRef | undefined,
  items: RecordRow[],
) {
  const [search, setSearch] = useState("");
  const [sort, setSort] = useState<GridSort | null>(null);

  useEffect(() => setSort(null), [entity?.name]);

  const fields = useMemo(() => entity?.fields ?? [], [entity]);
  const shown = useMemo(() => fields.filter((f) => f.type !== "id"), [fields]);
  const columns: GridColumn[] = useMemo(
    () =>
      shown.map((f) => ({
        key: f.name,
        header: humanize(f.name),
        align: isNumericType(f.type) ? "right" : "left",
      })),
    [shown],
  );
  const exportColumns = useMemo(() => fields.map((f) => f.name), [fields]);

  const displayed = useMemo(() => {
    const needle = search.trim().toLowerCase();
    const filtered = needle
      ? items.filter((row) =>
          fields.some((f) =>
            formatCell(row[f.name], f.type).toLowerCase().includes(needle),
          ),
        )
      : items;
    if (!sort) return filtered;
    const sign = sort.direction === "asc" ? 1 : -1;
    return [...filtered].sort(
      (a, b) => sign * compare(a[sort.key], b[sort.key]),
    );
  }, [items, fields, search, sort]);

  const toCells = (row: RecordRow) =>
    shown.map((f) => formatCell(row[f.name], f.type));

  const toggleSort = (key: string) =>
    setSort((current) =>
      current?.key !== key
        ? { key, direction: "asc" }
        : current.direction === "asc"
          ? { key, direction: "desc" }
          : null,
    );

  return {
    columns,
    exportColumns,
    displayed,
    toCells,
    search,
    setSearch,
    sort,
    toggleSort,
  };
}
