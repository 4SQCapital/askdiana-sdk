import * as React from "react";
import * as SwitchPrimitives from "@radix-ui/react-switch";
import { cn } from "../lib/cn";
import { useField } from "../lib/field-context";

export interface SwitchProps extends React.ComponentPropsWithoutRef<
  typeof SwitchPrimitives.Root
> {
  name?: string;
  label?: string;
}

export function Switch({
  name,
  label,
  className,
  checked,
  onCheckedChange,
  ...props
}: SwitchProps) {
  const field = useField(name);
  const isChecked = field ? Boolean(field.value) : checked;
  const handle = field ? (c: boolean) => field.setValue(c) : onCheckedChange;

  const control = (
    <SwitchPrimitives.Root
      id={name}
      checked={isChecked}
      onCheckedChange={handle}
      className={cn(
        "peer inline-flex h-5 w-9 shrink-0 cursor-pointer items-center rounded-full border-2 border-transparent shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 data-[state=checked]:bg-primary data-[state=unchecked]:bg-input",
        className,
      )}
      {...props}
    >
      <SwitchPrimitives.Thumb className="pointer-events-none block h-4 w-4 rounded-full bg-background shadow-lg ring-0 transition-transform data-[state=checked]:translate-x-4 data-[state=unchecked]:translate-x-0" />
    </SwitchPrimitives.Root>
  );

  if (!label) return control;
  return (
    <div className="flex items-center justify-between py-1.5">
      <label htmlFor={name} className="text-sm font-medium leading-none">
        {label}
      </label>
      {control}
    </div>
  );
}
