import { useEffect, useMemo, useState } from "react";

export interface Pagination<T> {
  page: number;
  pageCount: number;
  pageItems: T[];
  start: number;
  end: number;
  total: number;
  setPage: (page: number) => void;
}

export function usePagination<T>(
  items: T[],
  pageSize: number,
  resetKey: unknown = null,
): Pagination<T> {
  const [page, setPage] = useState(1);
  const pageCount = Math.max(1, Math.ceil(items.length / pageSize));
  const current = Math.min(page, pageCount);

  useEffect(() => setPage(1), [resetKey]);

  return useMemo(() => {
    const start = (current - 1) * pageSize;
    const pageItems = items.slice(start, start + pageSize);
    return {
      page: current,
      pageCount,
      pageItems,
      start,
      end: start + pageItems.length,
      total: items.length,
      setPage: (next: number) =>
        setPage(Math.min(Math.max(1, next), pageCount)),
    };
  }, [items, pageSize, current, pageCount]);
}
