import { useEffect, useState } from "react";
import { getJson } from "../lib/api";

export interface FetchState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
}

export function useFetch<T>(
  path: string | null,
  params: Record<string, string>,
  refreshKey = 0,
): FetchState<T> {
  const [state, setState] = useState<FetchState<T>>({
    data: null,
    loading: false,
    error: null,
  });
  const paramsKey = JSON.stringify(params);

  useEffect(() => {
    if (!path) return;
    const ctrl = new AbortController();
    setState((s) => ({ ...s, loading: true, error: null }));
    getJson<T>(path, JSON.parse(paramsKey), ctrl.signal)
      .then((data) => setState({ data, loading: false, error: null }))
      .catch((e: Error) => {
        if (e.name !== "AbortError")
          setState((s) => ({ ...s, loading: false, error: e.message }));
      });
    return () => ctrl.abort();
  }, [path, paramsKey, refreshKey]);

  return state;
}
