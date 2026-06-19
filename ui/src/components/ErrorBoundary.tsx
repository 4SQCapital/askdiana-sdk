import React from "react";

export class ErrorBoundary extends React.Component<
  { label?: string; children: React.ReactNode },
  { hasError: boolean }
> {
  state = { hasError: false };
  static getDerivedStateFromError() {
    return { hasError: true };
  }
  render() {
    if (this.state.hasError) {
      return (
        <div className="rounded-md border border-dashed border-destructive/40 p-2 text-sm text-destructive">
          {this.props.label || "This view could not be displayed."}
        </div>
      );
    }
    return this.props.children;
  }
}
