import React, { useState } from "react";
import { FieldContext } from "../lib/field-context";
import { ErrorBoundary } from "./ErrorBoundary";
import { Button } from "./Button";
import { bridge } from "../bridge";

export interface SettingsProps {
  children: React.ReactNode;
  initialValues?: Record<string, unknown>;
  title?: string;
  onSaved?: (values: Record<string, unknown>) => void;
}

export function Settings({
  children,
  initialValues = {},
  title = "Settings",
  onSaved,
}: SettingsProps) {
  const [values, setValues] = useState<Record<string, unknown>>(initialValues);
  const [saving, setSaving] = useState(false);
  const setValue = (name: string, v: unknown) =>
    setValues((s) => ({ ...s, [name]: v }));
  const handleSave = () => {
    setSaving(true);
    bridge.save(values);
    onSaved?.(values);
    setSaving(false);
  };

  return (
    <ErrorBoundary>
      <FieldContext.Provider value={{ values, setValue }}>
        <div className="bg-background text-foreground p-4">
          <div className="flex flex-col gap-4">
            <h2 className="text-base font-semibold">{title}</h2>
            {children}
            <Button disabled={saving} onClick={handleSave}>
              {saving ? "Saving..." : "Save"}
            </Button>
          </div>
        </div>
      </FieldContext.Provider>
    </ErrorBoundary>
  );
}
