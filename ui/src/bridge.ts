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

  /**
   * Keep the host iframe sized to this document's content. Posts a `resize`
   * immediately and on every content-size change. Returns a disconnect fn.
   * Use in views the host embeds inline (e.g. the chat `response` view),
   * where a fixed iframe height would clip or letterbox the content.
   *
   * theme.css forces `html, body, #root { height: 100% }` and `#root {
   * overflow-y: auto }` — needed so views with a *fixed* host-provided
   * height (the right panel, the settings/app iframes) get their own
   * internal scrollbar instead of being clipped. An inline response view
   * has no fixed height — it should grow with its content instead — so
   * that constraint is exactly what breaks auto-resize: #root swallows
   * the overflow as its own internal scrollbar, and document.documentElement
   * never reports the real content height to the ResizeObserver below.
   * Temporarily lift it for as long as autoResize is active.
   *
   * The height is measured on #root, not on <html>: <html> is at least as
   * tall as the iframe itself, so measuring it lets the frame grow but never
   * shrink back (a chart that settles smaller left an empty gap). DOM changes
   * are watched too, because data replacing a skeleton is not always a resize
   * of the target, and reports are batched to one per frame.
   */
  autoResize(target?: HTMLElement): () => void {
    const root = document.getElementById("root");
    const measured = target ?? root ?? document.documentElement;
    const prevHtmlOverflow = document.documentElement.style.overflow;
    const prevBodyOverflow = document.body.style.overflow;
    const prevRootHeight = root?.style.height;
    const prevRootOverflowY = root?.style.overflowY;

    document.documentElement.style.overflow = "visible";
    document.body.style.overflow = "visible";
    if (root) {
      root.style.height = "auto";
      root.style.overflowY = "visible";
    }

    let last = 0;
    let frame = 0;
    const report = () => {
      frame = 0;
      const height = Math.ceil(measured.scrollHeight);
      if (height !== last) {
        last = height;
        bridge.resize(height);
      }
    };
    const schedule = () => {
      if (!frame) frame = requestAnimationFrame(report);
    };
    const ro = new ResizeObserver(schedule);
    ro.observe(measured);
    const mo = new MutationObserver(schedule);
    mo.observe(measured, { childList: true, subtree: true, attributes: true, characterData: true });
    report();

    return () => {
      ro.disconnect();
      mo.disconnect();
      if (frame) cancelAnimationFrame(frame);
      document.documentElement.style.overflow = prevHtmlOverflow;
      document.body.style.overflow = prevBodyOverflow;
      if (root) {
        root.style.height = prevRootHeight ?? "";
        root.style.overflowY = prevRootOverflowY ?? "";
      }
    };
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

  /**
   * Invoke another installed extension's own invocation capability from
   * within a Solution's UI. The host proxies this to `POST
   * /extensions/<targetInstallId>/invoke`, which only succeeds if THIS
   * extension's own manifest declares the target's slug under
   * `capabilities.can_invoke` — an unauthorized target rejects with an
   * error rather than silently doing nothing.
   */
  invokeExtension(
    targetInstallId: string,
    parameters?: Record<string, unknown>,
  ): Promise<unknown> {
    const id = Math.random().toString(36).slice(2);
    post("invoke-extension", { id, targetInstallId, parameters: parameters ?? {} });
    return new Promise((resolve, reject) => {
      function handler(e: MessageEvent) {
        const msg = e.data;
        if (
          msg?.source === "askdiana-host" &&
          msg.type === "invoke-extension-response" &&
          msg.payload?.id === id
        ) {
          window.removeEventListener("message", handler);
          if (msg.payload.error) reject(new Error(msg.payload.error));
          else resolve(msg.payload.result);
        }
      }
      window.addEventListener("message", handler);
    });
  },
};
