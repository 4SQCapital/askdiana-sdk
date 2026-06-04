import * as React from "react";
import { cn } from "../lib/cn";
import { useField } from "../lib/field-context";

export interface InputProps extends React.ComponentProps<"input"> {
  name?: string;
}

export function Input({
  name,
  className,
  type,
  value,
  onChange,
  ...props
}: InputProps) {
  const field = useField(name);
  const bound = field
    ? {
        value: String(field.value ?? ""),
        onChange: (e: React.ChangeEvent<HTMLInputElement>) =>
          field.setValue(
            type === "number" ? Number(e.target.value) : e.target.value,
          ),
      }
    : { value, onChange };
  return (
    <input
      id={name}
      name={name}
      type={type}
      className={cn(
        "flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm transition-colors placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50",
        className,
      )}
      {...props}
      {...bound}
    />
  );
}
