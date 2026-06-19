import React from "react";

interface TextProps {
  children?: React.ReactNode;
  content?: string;
}

export function Text({ children, content }: TextProps) {
  return (
    <p className="test-sm leading-relaxed text-foreground">
      {content ?? children}
    </p>
  );
}
