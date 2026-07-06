import * as SelectPrimitive from "@radix-ui/react-select";
import { Check, ChevronDown } from "lucide-react";
import { cn } from "../lib/cn";
import { useField } from "../lib/field-context";

type Option = { value: string; label: string } | string;
export interface SelectProps {
  name?: string;
  value?: string;
  onValueChange?: (v: string) => void;
  options?: Option[];
  placeholder?: string;
  className?: string;
  /** Extra className applied to the dropdown content panel. */
  contentClassName?: string;
  /** Inline style applied to the dropdown content panel (e.g. to match a custom background). */
  contentStyle?: Record<string, string>;
}

export function Select({
  name,
  value,
  onValueChange,
  options = [],
  placeholder = "Select…",
  className,
  contentClassName,
  contentStyle,
}: SelectProps) {
  const field = useField(name);
  const val = field ? String(field.value ?? "") : value;
  const change = field ? (v: string) => field.setValue(v) : onValueChange;

  return (
    <SelectPrimitive.Root value={val} onValueChange={change}>
      <SelectPrimitive.Trigger
        id={name}
        className={cn(
          "flex h-9 w-full items-center justify-between rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-ring disabled:cursor-not-allowed disabled:opacity-50 [&>span]:line-clamp-1",
          className,
        )}
      >
        <SelectPrimitive.Value placeholder={placeholder} />
        <SelectPrimitive.Icon asChild>
          <ChevronDown className="h-4 w-4 opacity-50" />
        </SelectPrimitive.Icon>
      </SelectPrimitive.Trigger>
      <SelectPrimitive.Portal>
        <SelectPrimitive.Content
          position="popper"
          className={cn(
            "relative z-50 max-h-96 w-[var(--radix-select-trigger-width)] overflow-hidden rounded-md border bg-popover text-popover-foreground shadow-md data-[side=bottom]:translate-y-1",
            contentClassName,
          )}
          style={contentStyle}
        >
          <SelectPrimitive.Viewport className="p-1">
            {options.map((o) => {
              const v = typeof o === "string" ? o : o.value;
              const l = typeof o === "string" ? o : o.label;
              return (
                <SelectPrimitive.Item
                  key={v}
                  value={v}
                  className="relative flex w-full cursor-default select-none items-center rounded-sm py-1.5 pl-2 pr-8 text-sm outline-none focus:bg-white/20 data-[disabled]:pointer-events-none data-[disabled]:opacity-50"
                >
                  <span className="absolute right-2 flex h-3.5 w-3.5 items-center justify-center">
                    <SelectPrimitive.ItemIndicator>
                      <Check className="h-4 w-4" />
                    </SelectPrimitive.ItemIndicator>
                  </span>
                  <SelectPrimitive.ItemText>{l}</SelectPrimitive.ItemText>
                </SelectPrimitive.Item>
              );
            })}
          </SelectPrimitive.Viewport>
        </SelectPrimitive.Content>
      </SelectPrimitive.Portal>
    </SelectPrimitive.Root>
  );
}
