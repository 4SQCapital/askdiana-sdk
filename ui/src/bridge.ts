export interface InitData {
  installId: string;
  view: string;
  theme?: { colorScheme?: "light" | "dark"; [k: string]: unknown };
  config?: Record<string, unknown>;
  params?: Record<string, unknown>;
  /** Signed user + persona from the platform; absent on older hosts. See `bridge.fetch`. */
  context?: string | null;
}

/** What the signed context says, decoded for display. Your backend verifies the token itself. */
export interface ContextUser {
  userId: string;
  name: string | null;
  email: string | null;
  persona: { id: string; name: string; adminManaged: boolean } | null;
  expiresAt: number;
}

const HOST_ORIGIN = "*"; // tighten to your host origin in production
const CONTEXT_HEADER = "X-AskDiana-Context";

let context: string | null = null;
const contextListeners = new Set<(user: ContextUser | null) => void>();

function setContext(token: unknown) {
  if (typeof token !== "string" || !token || token === context) return;
  context = token;
  const user = bridge.user();
  contextListeners.forEach((fn) => fn(user));
}

function decodeClaims(token: string): Record<string, unknown> | null {
  try {
    const part = token.split(".")[1].replace(/-/g, "+").replace(/_/g, "/");
    const json = decodeURIComponent(
      Array.from(atob(part.padEnd(part.length + ((4 - (part.length % 4)) % 4), "=")))
        .map((c) => "%" + c.charCodeAt(0).toString(16).padStart(2, "0"))
        .join(""),
    );
    return JSON.parse(json);
  } catch {
    return null;
  }
}

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
      if (msg.type === "init") {
        setContext((msg.payload as InitData)?.context);
        onInit(msg.payload as InitData);
      } else if (msg.type === "context") {
        setContext((msg.payload as { context?: string } | undefined)?.context);
      }
    });
    post("ready");
  },

  /** The signed context token, or null when the host sent none (an older platform, local preview). */
  context(): string | null {
    return context;
  },

  /** Who is using the view and in which persona, for display only; your backend must verify the token. */
  user(): ContextUser | null {
    const claims = context ? decodeClaims(context) : null;
    if (!claims) return null;
    const persona = claims.persona as { id?: string; name?: string; kind?: string } | null | undefined;
    return {
      userId: String(claims.sub ?? ""),
      name: (claims.name as string) ?? null,
      email: (claims.email as string) ?? null,
      persona: persona?.id
        ? {
            id: String(persona.id),
            name: String(persona.name ?? ""),
            adminManaged: persona.kind === "admin_managed",
          }
        : null,
      expiresAt: Number(claims.exp ?? 0),
    };
  },

  /** Called when the context arrives, is renewed, or the user switches persona. Returns an unsubscribe fn. */
  onContext(fn: (user: ContextUser | null) => void): () => void {
    contextListeners.add(fn);
    return () => contextListeners.delete(fn);
  },

  /**
   * `fetch` that sends the signed context in `X-AskDiana-Context`, so your backend knows
   * the user and persona (`request_context()` in the Python SDK). Use it for calls to your
   * extension's own API. Without a context it is plain `fetch`.
   */
  fetch(input: RequestInfo | URL, init: RequestInit = {}): Promise<Response> {
    if (!context) return fetch(input, init);
    const headers = new Headers(init.headers);
    headers.set(CONTEXT_HEADER, context);
    return fetch(input, { ...init, headers });
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
   * Ask the host to open a dialog over the whole app showing this
   * extension's `?view=modal`, with `request` as that view's `init.params`.
   * Works from the side panel and from chat response views, which can't
   * draw outside their own frame. Resolves true when the host confirms
   * (`modal-opened`), false otherwise (an older host): show your own
   * dialog then.
   */
  openModal(
    request: { modal: string; size?: "md" | "xl" } & Record<string, unknown>,
    timeoutMs = 600,
  ): Promise<boolean> {
    if (window.parent === window) return Promise.resolve(false);
    return new Promise((resolve) => {
      const finish = (ok: boolean) => {
        window.removeEventListener("message", onMessage);
        clearTimeout(timer);
        resolve(ok);
      };
      const onMessage = (e: MessageEvent) => {
        const msg = e.data;
        if (
          e.source === window.parent &&
          msg?.source === "askdiana-host" &&
          msg.type === "modal-opened"
        )
          finish(true);
      };
      const timer = setTimeout(() => finish(false), timeoutMs);
      window.addEventListener("message", onMessage);
      post("open-modal", request);
    });
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
    const prevRootDisplay = root?.style.display;

    document.documentElement.style.overflow = "visible";
    document.body.style.overflow = "visible";
    if (root) {
      root.style.height = "auto";
      root.style.overflowY = "visible";
      // Contain the children's margins: otherwise the first and last child's
      // margins collapse through #root, sit outside its box, and are missed.
      root.style.display = "flow-root";
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
        root.style.display = prevRootDisplay ?? "";
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
