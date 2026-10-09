import type { ReactNode } from "react";
import { Button, cn } from "askdiana-ui";

interface IconButtonProps {
  label: string;
  onClick: () => void;
  children: ReactNode;
  disabled?: boolean;
  spinning?: boolean;
  className?: string;
}

/** Square button with an icon only. `label` is the tooltip and the screen-reader name. */
export function IconButton({
  label,
  onClick,
  children,
  disabled,
  spinning,
  className,
}: IconButtonProps) {
  return (
    <Button
      type="button"
      variant="ghost"
      size="icon"
      aria-label={label}
      title={label}
      onClick={onClick}
      disabled={disabled}
      className={cn(
        "h-8 w-8 sm:h-8 sm:w-8",
        spinning && "[&_svg]:animate-spin",
        className,
      )}
    >
      {children}
    </Button>
  );
}
