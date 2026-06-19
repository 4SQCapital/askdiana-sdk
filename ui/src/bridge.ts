export interface InitData {
  installId: string;
  view: string;
  theme?: { colorScheme?: "light" | "dark"; [k: string]: unknown };
  config?: Record<string, unknown>;
  params?: Record<string, unknown>;
}

const HOST_ORIGIN = "*"; // tighten to your host origin in production

function post(type: string, payload?: unknown) {
  window.parent?.postMessage(
    { source: "askdiana-ui", type, payload },
    HOST_ORIGIN,
  );
}

export const bridge = {
  /** Announce readiness and receive the host's init payload. */
  ready(onInit: (data: InitData) => void) {
    window.addEventListener("message", (e) => {
      const msg = e.data;
      if (!msg || msg.source !== "askdiana-host") return;
      if (msg.type === "init") onInit(msg.payload as InitData);
    });
    post("ready");
  },
  save(values: Record<string, unknown>) {
    post("save", values);
  },
  submit(values: Record<string, unknown>) {
    post("submit", values);
  },
  close() {
    post("close");
  },
  resize(height: number) {
    post("resize", { height });
  },

  /** Ask the host to resolve a dynamic-options `source` path. */
  requestOptions(path: string): Promise<{ value: string; label: string }[]> {
    const id = Math.random().toString(36).slice(2);
    post("options-request", { id, path });
    return new Promise((resolve) => {
      function handler(e: MessageEvent) {
        const msg = e.data;
        if (
          msg?.source === "askdiana-host" &&
          msg.type === "options-response" &&
          msg.payload?.id === id
        ) {
          window.removeEventListener("message", handler);
          resolve(msg.payload.options || []);
        }
      }
      window.addEventListener("message", handler);
    });
  },
};
