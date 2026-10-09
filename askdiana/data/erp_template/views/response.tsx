import { Response, registerBlock, type InitData } from "askdiana-ui";
import { isChartType } from "./components/charts/chartTypes";
import { ChartView } from "./components/charts/ChartView";
import { DataGrid } from "./components/table/DataGrid";
import { Pagination } from "./components/table/Pagination";
import { useMeta } from "./hooks/useErpData";
import { usePagination } from "./hooks/usePagination";
import { setCurrency } from "./lib/format";
import type { ChartPoint } from "./types/dashboard";

const DEFAULT_PAGE_SIZE = 10;

interface ChartBlock {
  chart_type?: string;
  title?: string;
  data?: ChartPoint[];
}

interface TableBlock {
  headers?: string[];
  rows?: string[][];
  total_count?: number;
  page_size?: number;
}

registerBlock("text", (b, k) => {
  if (b.style === "heading")
    return (
      <h3 key={k} className="text-base font-semibold text-foreground">
        {b.content}
      </h3>
    );
  const weight = b.style === "bold" ? "font-semibold" : "leading-relaxed";
  return (
    <p key={k} className={`text-sm text-foreground ${weight}`}>
      {b.content}
    </p>
  );
});

registerBlock("chart", (b, k) => (
  <ResponseChart key={k} block={b as ChartBlock} />
));
registerBlock("table", (b, k) => (
  <ResponseTable key={k} block={b as TableBlock} />
));

function ResponseChart({ block }: { block: ChartBlock }) {
  return (
    <figure className="space-y-1">
      {block.title && (
        <figcaption className="text-sm font-semibold text-foreground">
          {block.title}
        </figcaption>
      )}
      <ChartView
        type={isChartType(block.chart_type) ? block.chart_type : undefined}
        data={block.data ?? []}
      />
    </figure>
  );
}

function ResponseTable({ block }: { block: TableBlock }) {
  const headers = block.headers ?? [];
  const rows = block.rows ?? [];
  const pager = usePagination(rows, block.page_size || DEFAULT_PAGE_SIZE);
  const capped =
    typeof block.total_count === "number" && block.total_count > rows.length;

  return (
    <div className="space-y-2">
      <DataGrid
        columns={headers.map((h, i) => ({ key: `${i}`, header: h }))}
        rows={pager.pageItems}
        rowKey={(i) => pager.start + i}
      />
      {typeof block.page_size === "number" && (
        <Pagination
          page={pager.page}
          pageCount={pager.pageCount}
          start={pager.start}
          end={pager.end}
          total={pager.total}
          onPage={pager.setPage}
          note={
            capped
              ? `${block.total_count} in total, download CSV for the rest`
              : undefined
          }
        />
      )}
    </div>
  );
}

export default function ChatResponse({
  init,
  installId,
}: {
  init: InitData;
  installId: string;
}) {
  // Charts format money in the pack's currency, which only /api/meta knows. Wait for it (it is cached and
  // quick) rather than drawing in dollars and redrawing: each redraw resized the chat message.
  const meta = useMeta(installId, 0);
  if (installId && !meta.data && !meta.error) return null;
  setCurrency(meta.data?.currency);
  const blocks = init.params?.blocks as unknown[] | undefined;
  if (blocks?.length) return <Response blocks={blocks as never} />;

  const content = init.params?.content as string | undefined;
  if (content) {
    try {
      const parsed = JSON.parse(content);
      if (parsed?.type === "rich_response")
        return <Response blocks={parsed.blocks} />;
    } catch {}
    return (
      <Response>
        <p className="whitespace-pre-wrap text-sm leading-relaxed text-foreground">
          {content}
        </p>
      </Response>
    );
  }

  return (
    <Response>
      <p className="text-sm text-muted-foreground">
        No response data received.
      </p>
    </Response>
  );
}
