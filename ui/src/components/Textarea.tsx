import * as React from "react";
import { cn } from "../lib/cn";
import { useField } from "../lib/field-context";

export interface TextareaProps extends React.ComponentProps<"textarea"> {
  name?: string;
}

export function Textarea({
  name,
  className,
  value,
  onChange,
  ...props
}: TextareaProps) {
  const field = useField(name);
  const bound = field
    ? {
        value: String(field.value ?? ""),
        onChange: (e: React.ChangeEvent<HTMLTextAreaElement>) =>
          field.setValue(e.target.value),
      }
    : { value, onChange };
  return (
    <textarea
      id={name}
      name={name}
      className={cn(
        "flex min-h-[80px] w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50",
        className,
      )}
      {...props}
      {...bound}
    />
  );
}
