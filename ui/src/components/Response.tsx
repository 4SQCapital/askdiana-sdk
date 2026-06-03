import React from "react";
import { getRenderer } from "./blocks/registry";
import { ErrorBoundary } from "./ErrorBoundary";

export interface ResponseProps {
  content?: string; // JSON string: { type: "rich_response", blocks: [...] }
  blocks?: any[]; // or pass blocks directly
}

export function Response({ content, blocks }: ResponseProps) {
  let list = blocks;
  if (!list && content) {
    try {
      const parsed = JSON.parse(content);
      if (parsed?.type === "rich_response") list = parsed.blocks;
    } catch {
      /* not JSON → render nothing */
    }
  }
  if (!list || !list.length) return null;

  return (
    <div className="ext-root">
      {list.map((block, i) => {
        const renderer = getRenderer(block?.type);
        if (!renderer)
          return (
            <div key={i} className="ext-error">
              Unknown block: {String(block?.type)}
            </div>
          );
        return (
          <ErrorBoundary
            key={i}
            label="This block could not be displayed."
            hasError={false}
          >
            {renderer(block, i)}
          </ErrorBoundary>
        );
      })}
    </div>
  );
}
