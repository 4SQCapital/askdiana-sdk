import type { ReactNode } from "react";
import { cn } from "askdiana-ui";
import { AlertIcon, InfoIcon } from "../ui/icons";

const TONES = {
  info: {
    className:
      "border-blue-200 bg-blue-50 text-blue-900 dark:border-blue-900 dark:bg-blue-950/60 dark:text-blue-100",
    Icon: InfoIcon,
  },
  warning: {
    className:
      "border-amber-200 bg-amber-50 text-amber-900 dark:border-amber-900 dark:bg-amber-950/60 dark:text-amber-100",
    Icon: AlertIcon,
  },
  error: {
    className:
      "border-red-200 bg-red-50 text-red-900 dark:border-red-900 dark:bg-red-950/60 dark:text-red-100",
    Icon: AlertIcon,
  },
} as const;

interface BannerProps {
  tone?: keyof typeof TONES;
  children: ReactNode;
  action?: ReactNode;
}

export function Banner({ tone = "info", children, action }: BannerProps) {
  const { className, Icon } = TONES[tone];
  return (
    <div
      role={tone === "error" ? "alert" : "status"}
      className={cn(
        "flex items-center gap-2 rounded-lg border px-3 py-2 text-xs",
        className,
      )}
    >
      <Icon className="shrink-0" />
      <div className="flex-1">{children}</div>
      {action}
    </div>
  );
}
