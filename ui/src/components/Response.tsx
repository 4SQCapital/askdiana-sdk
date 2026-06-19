import React from "react";
import { getRenderer } from "./blocks/registry";
import { ErrorBoundary } from "./ErrorBoundary";

export interface ResponseProps {
  content?: string; // JSON string: { type: "rich_response", blocks: [...] }
  blocks?: any[]; // or pass blocks directly
  children?: React.ReactNode; // or hand-author with <Text/> <List/> ...
}

export function Response({ content, blocks, children }: ResponseProps) {
  // Composition mode: author block tags by hand.
  if (children)
    return (
      <div className="space-y-3 bg-background p-4 text-foreground">
        {children}
      </div>
    );

  // Data mode: render blocks the extension's backend returned.
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
    <div className="space-y-3 bg-background p-4 text-foreground">
      {list.map((block, i) => {
        const renderer = getRenderer(block?.type);
        return (
          <ErrorBoundary key={i} label="This block could not be displayed.">
            {renderer ? (
              renderer(block, i)
            ) : (
              <div className="text-sm text-destructive">
                Unknown block: {String(block?.type)}
              </div>
            )}
          </ErrorBoundary>
        );
      })}
    </div>
  );
}
