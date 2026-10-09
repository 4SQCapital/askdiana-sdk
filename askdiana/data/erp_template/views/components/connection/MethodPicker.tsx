import { cn } from "askdiana-ui";
import type { ConnectOption } from "../../types/connection";

interface MethodPickerProps {
  options: ConnectOption[];
  value: string;
  onChange: (method: string) => void;
}

/** Radio list of the login methods in one group; only the chosen method's form is shown below it. */
export function MethodPicker({ options, value, onChange }: MethodPickerProps) {
  return (
    <div role="radiogroup" aria-label="How to sign in" className="space-y-1.5">
      <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">How to sign in</p>
      {options.map((option) => {
        const checked = option.method === value;
        return (
          <button
            key={option.method}
            type="button"
            role="radio"
            aria-checked={checked}
            onClick={() => onChange(option.method)}
            className={cn(
              "flex w-full items-center gap-3 rounded-lg border px-3 py-2 text-left text-sm transition-colors",
              checked ? "border-primary bg-primary/5 font-medium" : "hover:bg-muted/60",
            )}
          >
            <span
              className={cn(
                "flex h-4 w-4 flex-none items-center justify-center rounded-full border",
                checked ? "border-primary" : "border-muted-foreground/40",
              )}
            >
              {checked && <span className="h-2 w-2 rounded-full bg-primary" />}
            </span>
            {option.label}
          </button>
        );
      })}
    </div>
  );
}
