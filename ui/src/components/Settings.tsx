import React, { useState } from "react";
import { FieldContext } from "./FormField";
import { bridge } from "../bridge";
import { ErrorBoundary } from "./ErrorBoundary";

export interface SettingsProps {
  children: React.ReactNode;
  initialValues: Record<string, unknown>;
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
  const setValue = (name: string, value: unknown) =>
    setValues((prev) => ({ ...prev, [name]: value }));

  const handleSave = () => {
    setSaving(true);
    bridge.save(values); // host persists via updateInstallConfig
    onSaved?.(values);
    setSaving(false);
  };

  return (
    <ErrorBoundary hasError={false}>
      <FieldContext.Provider value={{ values, setValue }}>
        <div className="ext-root">
          <div className="ext-card">
            <h2 className="ext-title">{title}</h2>
            {children}
            <button
              className="ext-btn-primary"
              disabled={saving}
              onClick={handleSave}
            >
              {saving ? "Saving..." : "Save"}
            </button>
          </div>
        </div>
      </FieldContext.Provider>
    </ErrorBoundary>
  );
}
