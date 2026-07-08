import React from "react";

interface TextProps {
  children?: React.ReactNode;
  content?: string;
}

export function Text({ children, content }: TextProps) {
  return (
    <p className="text-sm leading-relaxed text-foreground">
      {content ?? children}
    </p>
  );
}
