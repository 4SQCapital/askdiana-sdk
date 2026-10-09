import { Button } from "askdiana-ui";
import { ChevronLeftIcon, ChevronRightIcon } from "../ui/icons";

interface PaginationProps {
  page: number;
  pageCount: number;
  start: number;
  end: number;
  total: number;
  onPage: (page: number) => void;
  note?: string;
}

export function Pagination({
  page,
  pageCount,
  start,
  end,
  total,
  onPage,
  note,
}: PaginationProps) {
  if (!total) return null;
  return (
    <div className="flex flex-wrap items-center justify-between gap-2 text-xs text-muted-foreground">
      <span>
        Showing {start + 1}–{end} of {total}
        {note && ` · ${note}`}
      </span>
      {pageCount > 1 && (
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            disabled={page <= 1}
            onClick={() => onPage(page - 1)}
          >
            <ChevronLeftIcon />
            Previous
          </Button>
          <span className="whitespace-nowrap tabular-nums">
            Page {page} of {pageCount}
          </span>
          <Button
            variant="outline"
            size="sm"
            disabled={page >= pageCount}
            onClick={() => onPage(page + 1)}
          >
            Next
            <ChevronRightIcon />
          </Button>
        </div>
      )}
    </div>
  );
}
