const REQUEST_HEADERS: HeadersInit = { "ngrok-skip-browser-warning": "1" };

export const API = {
  meta: "/api/meta",
  dashboard: "/api/dashboard",
  connection: "/api/connection",
  connect: "/api/connect",
  connectOAuth: "/connect/oauth",
  records: (entity: string) => `/api/${encodeURIComponent(entity)}`,
} as const;

function backendBase(): string {
  const injected = (window as { __EXT_API_BASE__?: string }).__EXT_API_BASE__;
  if (injected) return window.location.origin + injected.replace(/\/$/, "");
  return (import.meta.env.VITE_BACKEND_URL ?? "").replace(/\/$/, "");
}

export const BACKEND = backendBase();

export async function getJson<T>(
  path: string,
  params: Record<string, string>,
  signal?: AbortSignal,
): Promise<T> {
  const query = new URLSearchParams(params).toString();
  const res = await fetch(`${BACKEND}${path}?${query}`, {
    headers: REQUEST_HEADERS,
    signal,
  });
  const body = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(body.error ?? `${res.status} on ${path}`);
  return body as T;
}

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
    readonly kind?: string,
  ) {
    super(message);
  }
}

export async function postJson<T>(
  path: string,
  body: Record<string, unknown>,
): Promise<T> {
  const res = await fetch(`${BACKEND}${path}`, {
    method: "POST",
    headers: { ...REQUEST_HEADERS, "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok)
    throw new ApiError(
      data.error ?? `${res.status} on ${path}`,
      res.status,
      data.kind,
    );
  return data as T;
}
