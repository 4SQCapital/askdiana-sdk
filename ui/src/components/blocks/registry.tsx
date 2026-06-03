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
registerBlock("text", (block, key) => (
  <p key={key} className="ext-text">
    {block.content}
  </p>
));
registerBlock("divider", (_block, key) => <hr key={key} />);
registerBlock("alert", (block, key) => (
  <div key={key} className={`ext-alert ext-alert-${block.variant || "info"}`}>
    {block.content ?? block.message}
  </div>
));
registerBlock("image", (block, key) => (
  <figure key={key}>
    <img
      src={block.url}
      alt={block.alt || ""}
      style={{ maxWidth: "100%", borderRadius: 8 }}
    />
    {block.caption && (
      <figcaption className="ext-muted">{block.caption}</figcaption>
    )}
  </figure>
));
registerBlock("list", (block, key) => {
  const items = (block.items || []).map((it: string, i: number) => (
    <li key={i}>{it}</li>
  ));
  return block.ordered ? (
    <ol key={key}>{items}</ol>
  ) : (
    <ul key={key}>{items}</ul>
  );
});
registerBlock("code", (block, key) => (
  <pre
    key={key}
    style={{
      background: "var(--ext-muted)",
      padding: 12,
      borderRadius: 8,
      overflow: "auto",
    }}
  >
    <code>{block.content}</code>
  </pre>
));
registerBlock("card", (block, key) => (
  <div
    key={key}
    style={{
      border: "1px solid var(--ext-border)",
      borderRadius: 8,
      padding: 12,
      borderLeft: block.accent ? `3px solid ${block.accent}` : undefined,
    }}
  >
    {block.title && <strong>{block.title}</strong>}
    {block.body && <p className="ext-text">{block.body}</p>}
  </div>
));
registerBlock("table", (block, key) => (
  <table key={key} style={{ borderCollapse: "collapse", width: "100%" }}>
    <thead>
      <tr>
        {(block.headers || []).map((h: string, i: number) => (
          <th
            key={i}
            style={{
              textAlign: "left",
              borderBottom: "1px solid var(--ext-border)",
              padding: 6,
            }}
          >
            {h}
          </th>
        ))}
      </tr>
    </thead>
    <tbody>
      {(block.rows || []).map((row: string[], ri: number) => (
        <tr key={ri}>
          {row.map((c, ci) => (
            <td key={ci} style={{ padding: 6 }}>
              {c}
            </td>
          ))}
        </tr>
      ))}
    </tbody>
  </table>
));
