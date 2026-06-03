import React, { useState } from "react";
import { bridge } from "../bridge";
import { ErrorBoundary } from "./ErrorBoundary";
import { FieldContext } from "./FormField";

export interface ParameterModalProps {
  children: React.ReactNode;
  initialValues?: Record<string, unknown>;
  title?: string;
  submitLabel?: string;
  advanced?: React.ReactNode; // optional advanced section, collapsed by default
  onSubmit: (values: Record<string, unknown>) => void;
}

export function ParameterModel({
  children,
  initialValues = {},
  title = "Run extension",
  submitLabel = "Run",
  advanced,
  onSubmit,
}: ParameterModalProps) {
  const [values, setValues] = useState<Record<string, unknown>>(initialValues);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const setValue = (name: string, value: unknown) =>
    setValues((prev) => ({ ...prev, [name]: value }));

  const handleSubmit = () => {
    bridge.submit(values);
    onSubmit?.(values);
  };

  return (
    <ErrorBoundary hasError={false}>
      <FieldContext.Provider value={{ values, setValue }}>
        <div className="ext-root">
          <div className="ext-card">
            <h2 className="ext-title">{title}</h2>
            {children}
            {advanced && (
              <>
                <button
                  className="ext-advanced-toggle"
                  onClick={() => setShowAdvanced((s) => !s)}
                >
                  {showAdvanced
                    ? "Hide advanced options"
                    : "Show advanced options"}
                </button>
                {showAdvanced && <div>{advanced}</div>}
              </>
            )}
            <button className="ext-btn-primary" onClick={handleSubmit}>
              {submitLabel}
            </button>
          </div>
        </div>
      </FieldContext.Provider>
    </ErrorBoundary>
  );
}
