import React, { createContext, useContext } from "react";

export interface FieldContextValue {
  values: Record<string, unknown>;
  setValue: (name: string, value: unknown) => void;
}
export const FieldContext = createContext<FieldContextValue | null>(null);

type Option = { value: string; label: string } | string;

export interface FormFieldProps {
  name: string;
  type?:
    | "text"
    | "password"
    | "select"
    | "checkbox"
    | "number"
    | "textarea"
    | "url"
    | "email"
    | "color";
  label?: string;
  required?: boolean;
  placeholder?: string;
  options?: Option[];
  defaultValue?: unknown;
}

export function FormField(props: FormFieldProps) {
  const ctx = useContext(FieldContext);
  if (!ctx)
    throw new Error(
      "<FormField> must be used inside <Settings> or <ParameterModal>",
    );
  const { values, setValue } = ctx;
  const type = props.type ?? "text";
  const value =
    values[props.name] ??
    props.defaultValue ??
    (type === "checkbox" ? false : "");
  const set = (v: unknown) => setValue(props.name, v);

  const label = props.label && (
    <label className="ext-label" htmlFor={props.name}>
      {props.label}
      {props.required ? " *" : ""}
    </label>
  );

  if (type === "checkbox") {
    return (
      <div className="ext-field ext-field-row">
        {label}
        <input
          id={props.name}
          type="checkbox"
          checked={Boolean(value)}
          onChange={(e) => set(e.target.checked)}
        />
      </div>
    );
  }

  let control: React.ReactNode;
  switch (type) {
    case "textarea":
      control = (
        <textarea
          id={props.name}
          className="ext-textarea"
          value={String(value)}
          placeholder={props.placeholder}
          onChange={(e) => set(e.target.value)}
        />
      );
      break;
    case "select":
      control = (
        <select
          id={props.name}
          className="ext-select"
          value={String(value)}
          onChange={(e) => set(e.target.value)}
        >
          <option value="">{props.placeholder || "Select..."}</option>
          {(props.options || []).map((opt) => {
            const v = typeof opt === "string" ? opt : opt.value;
            const l = typeof opt === "string" ? opt : opt.label;
            return (
              <option key={v} value={v}>
                {l}
              </option>
            );
          })}
        </select>
      );
      break;
    case "number":
      control = (
        <input
          id={props.name}
          className="ext-input"
          type="number"
          value={String(value)}
          placeholder={props.placeholder}
          onChange={(e) => set(Number(e.target.value))}
        />
      );
      break;
    case "color":
      control = (
        <div style={{ display: "flex", gap: 8 }}>
          <input
            type="color"
            value={String(value || "#6366f1")}
            onChange={(e) => set(e.target.value)}
          />
          <input
            className="ext-input"
            type="text"
            value={String(value || "")}
            placeholder="#6366f1"
            onChange={(e) => set(e.target.value)}
          />
        </div>
      );
      break;
    default: // text, password, url, email
      control = (
        <input
          id={props.name}
          className="ext-input"
          type={type}
          value={String(value)}
          placeholder={props.placeholder}
          onChange={(e) => set(e.target.value)}
        />
      );
  }

  return (
    <div className="ext-field">
      {label}
      {control}
    </div>
  );
}
