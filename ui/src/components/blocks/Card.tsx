import React from "react";

interface CardProps {
  title?: string;
  body?: string;
  accent?: string;
  children?: React.ReactNode;
}

export function Card({ title, body, accent, children }: CardProps) {
  return (
    <div
      className="rounded-md border border-border bg-card p-3 text-card-foreground"
      style={accent ? { borderLeft: `3px solid ${accent}` } : undefined}
    >
      {title && <div className="font-medium">{title}</div>}
      {body && <p className="mt-1 text-sm">{body}</p>}
      {children}
    </div>
  );
}
