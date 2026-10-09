const HOST_ORIGIN = "*";
const REPLY_TIMEOUT_MS = 10000;

export const IN_HOST = window.parent !== window;

export const HOST_REQUEST = {
  connectSession: "connect-session",
  connectOAuth: "connect-oauth",
  connectComplete: "connect-complete",
  disconnect: "disconnect",
  openModal: "open-modal",
} as const;

export type ModalRequest =
  | { modal: "connection"; size: "md" }
  | {
      modal: "chart";
      size: "xl";
      chart: import("../types/dashboard").DashboardChart;
    };

export function openHostModal(request: ModalRequest): void {
  postToHost(HOST_REQUEST.openModal, request);
}

export const HOST_EVENT = {
  connectSession: "connect-session",
  connectionChanged: "connection-changed",
  connectionError: "connection-error",
} as const;

export function postToHost(type: string, payload?: unknown): void {
  if (!IN_HOST) return;
  window.parent.postMessage(
    { source: "askdiana-ui", type, payload },
    HOST_ORIGIN,
  );
}

export function onHostMessage(
  type: string,
  handler: (payload: unknown) => void,
): () => void {
  const listener = (e: MessageEvent) => {
    const msg = e.data;
    if (msg?.source === "askdiana-host" && msg.type === type)
      handler(msg.payload);
  };
  window.addEventListener("message", listener);
  return () => window.removeEventListener("message", listener);
}

export function requestHost<T>(
  type: string,
  payload: unknown,
  replyType: string,
): Promise<T> {
  return new Promise((resolve, reject) => {
    if (!IN_HOST) {
      reject(new Error("Open this panel inside AskDiana to connect."));
      return;
    }
    const stop = () => {
      offReply();
      offError();
      clearTimeout(timer);
    };
    const offReply = onHostMessage(replyType, (p) => {
      stop();
      resolve(p as T);
    });
    const offError = onHostMessage(HOST_EVENT.connectionError, (p) => {
      stop();
      reject(
        new Error(
          (p as { message?: string } | undefined)?.message ??
            "AskDiana could not connect.",
        ),
      );
    });
    const timer = setTimeout(() => {
      stop();
      reject(
        new Error("AskDiana did not answer. Reload the panel and try again."),
      );
    }, REPLY_TIMEOUT_MS);
    postToHost(type, payload);
  });
}
