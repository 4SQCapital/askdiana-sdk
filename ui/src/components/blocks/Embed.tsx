import React, { useState } from "react";
import { ChevronDown, ChevronUp, ExternalLink } from "lucide-react";

export interface EmbedProps {
  url: string;
  title?: string;
  description?: string;
  aspectRatio?: "16:9" | "4:3" | "1:1" | "auto";
  allowFullscreen?: boolean;
}

const ASPECT_MAP: Record<string, string> = {
  "16:9": "56.25%",
  "4:3": "75%",
  "1:1": "100%",
  auto: "56.25%",
};

export function Embed({
  url,
  title,
  description,
  aspectRatio = "16:9",
  allowFullscreen = true,
}: EmbedProps) {
  const [expanded, setExpanded] = useState(true);
  const paddingTop = ASPECT_MAP[aspectRatio] ?? ASPECT_MAP["16:9"];

  return (
    <div className="w-full max-w-2xl overflow-hidden rounded-xl border border-border bg-card shadow-sm">
      {(title || description) && (
        <div className="flex items-center justify-between gap-3 border-b border-border px-4 py-3">
          <div className="min-w-0">
            {title && (
              <h4 className="truncate text-sm font-semibold text-card-foreground">
                {title}
              </h4>
            )}
            {description && (
              <p className="truncate text-xs text-muted-foreground">
                {description}
              </p>
            )}
          </div>
          <div className="flex shrink-0 items-center gap-1.5">
            <button
              type="button"
              className="rounded p-1 text-muted-foreground hover:text-foreground"
              onClick={() => window.open(url, "_blank")}
            >
              <ExternalLink className="h-3.5 w-3.5" />
            </button>
            <button
              type="button"
              className="rounded p-1 text-muted-foreground hover:text-foreground"
              onClick={() => setExpanded((e) => !e)}
            >
              {expanded ? (
                <ChevronUp className="h-3.5 w-3.5" />
              ) : (
                <ChevronDown className="h-3.5 w-3.5" />
              )}
            </button>
          </div>
        </div>
      )}
      {expanded && (
        <div className="relative w-full" style={{ paddingTop }}>
          <iframe
            src={url}
            className="absolute inset-0 h-full w-full border-0"
            allow={allowFullscreen ? "fullscreen" : ""}
            title={title || "Embedded content"}
            sandbox="allow-scripts allow-same-origin allow-popups allow-downloads allow-forms"
          />
        </div>
      )}
    </div>
  );
}
