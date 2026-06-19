import React, { useState } from "react";
import { FieldContext } from "../lib/field-context";
import { ErrorBoundary } from "./ErrorBoundary";
import { Button } from "./Button";
import { bridge } from "../bridge";

export interface ParameterModalProps {
  children: React.ReactNode;
  initialValues?: Record<string, unknown>;
  title?: string;
  submitLabel?: string;
  advanced?: React.ReactNode;
  onSubmit?: (values: Record<string, unknown>) => void;
}

export function ParameterModal({
  children,
  initialValues = {},
  title = "Run extension",
  submitLabel = "Run",
  advanced,
  onSubmit,
}: ParameterModalProps) {
  const [values, setValues] = useState<Record<string, unknown>>(initialValues);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const setValue = (name: string, v: unknown) =>
    setValues((s) => ({ ...s, [name]: v }));
  const handleSubmit = () => {
    bridge.submit(values);
    onSubmit?.(values);
  };

  return (
    <ErrorBoundary>
      <FieldContext.Provider value={{ values, setValue }}>
        <div className="bg-background text-foreground p-4">
          <div className="flex flex-col gap-4">
            <h2 className="text-base font-semibold">{title}</h2>
            {children}
            {advanced && (
              <>
                <button
                  className="text-left text-sm text-primary"
                  onClick={() => setShowAdvanced((s) => !s)}
                >
                  {showAdvanced ? "Hide advanced" : "Advanced options"}
                </button>
                {showAdvanced && (
                  <div className="flex flex-col gap-4">{advanced}</div>
                )}
              </>
            )}
            <Button onClick={handleSubmit}>{submitLabel}</Button>
          </div>
        </div>
      </FieldContext.Provider>
    </ErrorBoundary>
  );
}
