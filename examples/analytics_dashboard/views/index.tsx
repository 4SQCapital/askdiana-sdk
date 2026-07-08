// @ts-ignore: side-effect import of CSS module
import "./tailwind.css";
import React from "react";
import { createRoot } from "react-dom/client";
import { bridge, applyTheme, type InitData } from "askdiana-ui";
import AnalyticsApp from "./app";
import AnalyticsResponse from "./response";
import AnalyticsChart from "./chart";

const params = new URLSearchParams(location.search);
const view = params.get("view") || "app";
const installId = params.get("install_id") || "";

function App() {
  const [init, setInit] = React.useState(null as InitData | null);
  React.useEffect(() => {
    bridge.ready((data) => {
      applyTheme(data.theme);
      setInit(data);
    });
    // Inline-embedded views must drive the host iframe's height themselves.
    const stopResize = view === "response" ? bridge.autoResize() : undefined;
    // standalone fallback so it still renders when opened outside the host
    const t = setTimeout(
      () =>
        setInit(
          (s) => s ?? ({ installId, view, config: {}, params: {} } as InitData),
        ),
      400,
    );
    return () => {
      clearTimeout(t);
      stopResize?.();
    };
  }, []);

  if (!init)
    return <div className="p-4 text-sm text-muted-foreground">Loading...</div>;
  if (view === "response") return <AnalyticsResponse init={init} installId={installId} />;
  if (view === "chart") return <AnalyticsChart init={init} installId={installId} />;
  return <AnalyticsApp init={init} installId={installId} />;
}

createRoot(document.getElementById("root")!).render(<App />);
