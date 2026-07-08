// @ts-ignore: side-effect import of CSS module
import "./tailwind.css";
import React from "react";
import { createRoot } from "react-dom/client";
import { bridge, type InitData } from "askdiana-ui";
import NotesSettings from "./settings";
import NotesResponse from "./response";
import NotesApp from "./app";

const params = new URLSearchParams(location.search);
const view = params.get("view") || "settings";
const installId = params.get("install_id") || "";

function App() {
  const [init, setInit] = React.useState(null as InitData | null);
  React.useEffect(() => {
    bridge.ready((data) => {
      document.documentElement.classList.toggle(
        "dark",
        data.theme?.colorScheme === "dark",
      );
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
  if (view === "app") return <NotesApp init={init} installId={installId} />;
  if (view === "response")
    return <NotesResponse init={init} installId={installId} />;
  return <NotesSettings init={init} installId={installId} />;
}

createRoot(document.getElementById("root")!).render(<App />);
