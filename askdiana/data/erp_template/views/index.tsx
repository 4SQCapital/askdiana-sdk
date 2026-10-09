// @ts-ignore: side-effect import of CSS module
import "./tailwind.css";
// @ts-ignore: side-effect import of CSS module
import "./skin.css";
import React from "react";
import { createRoot } from "react-dom/client";
import { bridge, applyTheme, type InitData } from "askdiana-ui";
import DashboardApp from "./app";
import ModalView from "./features/modal/ModalView";
import ChatResponse from "./response";

const BRIDGE_TIMEOUT_MS = 400;

/**
 * Keep the host iframe as tall as the content: AskDiana's centered dialog and the chat response view.
 * Measured on #root, because <html> keeps the iframe's height (it could grow but never shrink back).
 * DOM changes are watched too: a resize alone can be missed when data replaces a skeleton.
 */
function fitContent(): () => void {
  const root = document.getElementById("root");
  if (!root) return () => {};
  const stopResize = bridge.autoResize(root);
  let last = 0;
  const report = () => {
    const height = Math.ceil(root.scrollHeight);
    if (height !== last) {
      last = height;
      bridge.resize(height);
    }
  };
  const changes = new MutationObserver(() => requestAnimationFrame(report));
  changes.observe(root, {
    childList: true,
    subtree: true,
    attributes: true,
    characterData: true,
  });
  return () => {
    changes.disconnect();
    stopResize();
  };
}
const params = new URLSearchParams(location.search);
const view = params.get("view") || "app";
const installId = params.get("install_id") || "";

// In a chat message the view sits on the chat itself, without its own page background (skin: html.inline-view).
if (view === "response") document.documentElement.classList.add("inline-view");

function Root() {
  const [init, setInit] = React.useState<InitData | null>(null);

  React.useEffect(() => {
    let connected = false;
    bridge.ready((data) => {
      connected = true;
      applyTheme(data.theme);
      document.documentElement.classList.toggle(
        "light",
        data.theme?.colorScheme !== "dark",
      );
      setInit(data);
    });
    const stopResize =
      view === "response" || view === "modal" ? fitContent() : undefined;
    const fallback = setTimeout(() => {
      if (connected) return;
      document.documentElement.classList.toggle(
        "dark",
        matchMedia("(prefers-color-scheme: dark)").matches,
      );
      setInit({ installId, view, config: {}, params: {} } as InitData);
    }, BRIDGE_TIMEOUT_MS);
    return () => {
      clearTimeout(fallback);
      stopResize?.();
    };
  }, []);

  if (!init)
    return <div className="p-4 text-sm text-muted-foreground">Loading…</div>;
  if (view === "response")
    return <ChatResponse init={init} installId={installId} />;
  if (view === "modal") return <ModalView init={init} installId={installId} />;
  return <DashboardApp init={init} installId={installId} />;
}

createRoot(document.getElementById("root")!).render(<Root />);
