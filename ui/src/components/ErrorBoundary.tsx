import React from "react";

interface ErrorBoundaryProps {
  label?: string;
  children: React.ReactNode;
  hasError: boolean;
}

export class ErrorBoundary extends React.Component<ErrorBoundaryProps> {
  state = { hasError: false };
  static getDerivedStateFromError() {
    return { hasError: true };
  }
  render() {
    if (this.state.hasError) {
      return (
        <div className="ext-error">
          {this.props.label || "This view could not be displayed."}
        </div>
      );
    }
    return this.props.children;
  }
}
