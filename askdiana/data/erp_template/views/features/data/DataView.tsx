import { useMemo, useState } from "react";
import { Button, Select } from "askdiana-ui";
import { Banner } from "../../components/feedback/Banner";
import { EmptyState } from "../../components/feedback/EmptyState";
import { ErrorState } from "../../components/feedback/ErrorState";
import { TableSkeleton } from "../../components/feedback/Skeletons";
import { Toolbar } from "../../components/layout/Toolbar";
import { DataGrid } from "../../components/table/DataGrid";
import { Pagination } from "../../components/table/Pagination";
import { DownloadIcon, TableIcon } from "../../components/ui/icons";
import { SearchInput } from "../../components/ui/SearchInput";
import { useRecords } from "../../hooks/useErpData";
import { usePagination } from "../../hooks/usePagination";
import { downloadCsv } from "../../lib/csv";
import type { EntityRef } from "../../types/dashboard";
import { useRecordTable } from "./useRecordTable";

const PAGE_SIZE = 15;

interface DataViewProps {
  installId: string;
  entities: EntityRef[];
  refreshKey: number;
  onRetry: () => void;
}

export function DataView({
  installId,
  entities,
  refreshKey,
  onRetry,
}: DataViewProps) {
  const [chosen, setEntityName] = useState("");
  const entity = entities.find((e) => e.name === chosen) ?? entities[0];
  const entityName = entity?.name ?? "";
  const { data, loading, error } = useRecords(
    installId,
    entityName,
    refreshKey,
  );
  const items = useMemo(() => data?.items ?? [], [data]);
  const table = useRecordTable(entity, items);
  const pager = usePagination(
    table.displayed,
    PAGE_SIZE,
    `${entityName}|${table.search}|${table.sort?.key}|${table.sort?.direction}`,
  );

  if (!entities.length) {
    return (
      <EmptyState
        icon={<TableIcon />}
        title="No data sets listed"
        description="This extension's SDK is too old to list its data sets. Update askdiana to see raw records."
      />
    );
  }

  const download = () =>
    downloadCsv(
      entity?.label ?? entityName,
      table.displayed,
      table.exportColumns,
    );

  return (
    <div className="space-y-3">
      <Toolbar
        start={
          <>
            <Select
              value={entityName}
              onValueChange={setEntityName}
              options={entities.map((e) => ({ value: e.name, label: e.label }))}
              className="h-9 w-[180px]"
            />
            <SearchInput
              value={table.search}
              onChange={table.setSearch}
              placeholder="Search records…"
              className="min-w-[180px] flex-1"
            />
          </>
        }
        end={
          <Button
            variant="outline"
            size="sm"
            onClick={download}
            disabled={!table.displayed.length}
          >
            <DownloadIcon />
            Download CSV
          </Button>
        }
      />

      {data?.truncated && (
        <Banner tone="warning">
          Only the first {data.count} records were loaded. Totals and exports
          may be incomplete.
        </Banner>
      )}

      {error && !loading ? (
        <ErrorState message={error} onRetry={onRetry} />
      ) : loading && !data ? (
        <TableSkeleton />
      ) : !table.displayed.length ? (
        <EmptyState
          icon={<TableIcon />}
          title={table.search ? "No matching records" : "No records"}
          description={
            table.search
              ? "Try a different search."
              : `There are no ${entity?.label.toLowerCase() ?? "records"} yet.`
          }
        />
      ) : (
        <div
          className={
            loading ? "space-y-3 opacity-60 transition-opacity" : "space-y-3"
          }
        >
          <DataGrid
            columns={table.columns}
            rows={pager.pageItems.map(table.toCells)}
            rowKey={(i) => pager.start + i}
            sort={table.sort}
            onSort={table.toggleSort}
          />
          <Pagination
            page={pager.page}
            pageCount={pager.pageCount}
            start={pager.start}
            end={pager.end}
            total={pager.total}
            onPage={pager.setPage}
            note={
              table.search ? `filtered from ${data?.count ?? 0}` : undefined
            }
          />
        </div>
      )}
    </div>
  );
}
