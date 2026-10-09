import { API } from "../lib/api";
import type { ConnectionPayload } from "../types/connection";
import type {
  DashboardPayload,
  MetaPayload,
  RecordsPayload,
} from "../types/dashboard";
import { useFetch } from "./useFetch";

export function useMeta(installId: string, refreshKey: number) {
  return useFetch<MetaPayload>(
    installId ? API.meta : null,
    { install_id: installId },
    refreshKey,
  );
}

export function useDashboard(
  installId: string,
  tabId: string,
  refreshKey: number,
) {
  const params: Record<string, string> = { install_id: installId };
  if (tabId) params.tab = tabId;
  return useFetch<DashboardPayload>(
    installId ? API.dashboard : null,
    params,
    refreshKey,
  );
}

export function useRecords(
  installId: string,
  entity: string,
  refreshKey: number,
) {
  return useFetch<RecordsPayload>(
    installId && entity ? API.records(entity) : null,
    { install_id: installId },
    refreshKey,
  );
}

export function useConnection(installId: string, refreshKey: number) {
  return useFetch<ConnectionPayload>(
    installId ? API.connection : null,
    { install_id: installId },
    refreshKey,
  );
}
