import React from "react";

interface CodeProps {
  children?: React.ReactNode;
  content?: string;
  language?: string;
}

export function Code({ children, content, language }: CodeProps) {
  return (
    <pre className="overflow-auto rounded-md bg-muted p-3 text-sm">
      <code>{content ?? children}</code>
    </pre>
  );
}
