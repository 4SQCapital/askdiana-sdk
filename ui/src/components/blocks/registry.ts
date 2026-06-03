import React from "react";

export type BlockRenderer = (block: any, key: React.Key) => React.ReactNode;
const registry = new Map<string, BlockRenderer>();

export function registerBlock(type: string, renderer: BlockRenderer) {
  registry.set(type, renderer);
}
export function getRenderer(type: string) {
  return registry.get(type);
}

// ---- built-in blocks ----
registerBlock("text", (block, key) =>
  React.createElement("p", { key, className: "ext-text" }, block.content),
);
registerBlock("divider", (_block, key) => React.createElement("hr", { key }));
registerBlock("alert", (block, key) =>
  React.createElement(
    "div",
    { key, className: `ext-alert ext-alert-${block.variant || "info"}` },
    block.content ?? block.message,
  ),
);
registerBlock("image", (block, key) =>
  React.createElement(
    "figure",
    { key, className: "ext-image-wrapper" },
    React.createElement("img", {
      src: block.src,
      alt: block.alt || "",
      style: { maxWidth: "100%", borderRadius: 8 } as React.CSSProperties,
    }),
    block.caption &&
      React.createElement(
        "figcaption",
        { className: "ext-muted" },
        block.caption,
      ),
  ),
);
registerBlock("list", (block, key) => {
  const items = (block.items || []).map((item: any, index: number) =>
    React.createElement("li", { key: index }, item),
  );

  return React.createElement(
    block.ordered ? "ol" : "ul",
    { key, className: "ext-list" },
    items,
  );
});
registerBlock("code", (block, key) =>
  React.createElement(
    "pre",
    {
      key,
      style: {
        background: "var(--ext-muted)",
        padding: 12,
        borderRadius: 8,
        overflow: "auto",
      } as React.CSSProperties,
    },
    React.createElement("code", null, block.code),
  ),
);
registerBlock("card", (block, key) =>
  React.createElement(
    "div",
    {
      key,
      style: {
        border: "1px solid var(--ext-border)",
        borderRadius: 8,
        padding: 12,
        borderLeft: block.accent ? `3px solid ${block.accent}` : undefined,
      } as React.CSSProperties,
    },
    block.title && React.createElement("strong", {}, block.title),
    block.content &&
      React.createElement("div", { className: "ext-text" }, block.content),
  ),
);
registerBlock("table", (block, key) =>
  React.createElement(
    "table",
    {
      key,
      style: {
        borderCollapse: "collapse",
        width: "100%",
      } as React.CSSProperties,
    },
    React.createElement(
      "thead",
      null,
      React.createElement(
        "tr",
        null,
        (block.headers || []).map((h: string, i: number) =>
          React.createElement(
            "th",
            {
              key: i,
              style: {
                textAlign: "left",
                borderBottom: "1px solid var(--ext-border)",
                padding: 6,
              } as React.CSSProperties,
            },
            h,
          ),
        ),
      ),
    ),
    React.createElement(
      "tbody",
      null,
      (block.rows || []).map((row: string[], ri: number) =>
        React.createElement(
          "tr",
          { key: ri },
          row.map((c: string, ci: number) =>
            React.createElement(
              "td",
              { key: ci, style: { padding: 6 } as React.CSSProperties },
              c,
            ),
          ),
        ),
      ),
    ),
  ),
);
