import React from "react";
import { ErrorBoundary } from "./ErrorBoundary";

export interface AppProps {
  children: React.ReactNode;
  title?: string;
  bare?: boolean;
}

export function App({ children, title, bare = false }: AppProps) {
  return (
    <ErrorBoundary label="This extension's UI could not be displayed.">
      <div className="ext-root">
        {bare ? (
          children
        ) : (
          <div className="ext-card">
            {title && <h2 className="ext-title">{title}</h2>}
            {children}
          </div>
        )}
      </div>
    </ErrorBoundary>
  );
}
