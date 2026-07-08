import React from "react";
import { ExternalLink } from "lucide-react";
import { Button } from "../Button";
import { cn } from "../../lib/cn";

export interface ButtonItemProps {
  label: string;
  url?: string;
  style?: "primary" | "secondary" | "outline" | "ghost" | "destructive";
  icon?: string;
  /**
   * Marks this link as a file download rather than a page to open. Skips
   * `target="_blank"` (which otherwise flashes an empty tab for a same-page
   * download) and adds the `download` attribute. Pass a string to suggest
   * a filename, or `true` to just mark it as a download.
   */
  download?: string | boolean;
}

const VARIANT_MAP: Record<
  string,
  "default" | "secondary" | "outline" | "ghost" | "destructive"
> = {
  primary: "default",
  secondary: "secondary",
  outline: "outline",
  ghost: "ghost",
  destructive: "destructive",
};

export function ButtonItem({ label, url, style = "outline", icon, download }: ButtonItemProps) {
  const isMail = url?.startsWith("mailto:");
  const isDownload = Boolean(download);
  return (
    <Button variant={VARIANT_MAP[style] ?? "outline"} size="sm" asChild={!!url}>
      {url ? (
        <a
          href={url}
          target={isMail || isDownload ? undefined : "_blank"}
          rel={isMail || isDownload ? undefined : "noopener noreferrer"}
          download={isDownload ? (typeof download === "string" ? download : "") : undefined}
        >
          {icon && <span className="mr-1.5">{icon}</span>}
          {label}
          {!isMail && !isDownload && <ExternalLink className="ml-1.5 h-3 w-3 opacity-60" />}
        </a>
      ) : (
        <>
          {icon && <span className="mr-1.5">{icon}</span>}
          {label}
        </>
      )}
    </Button>
  );
}

export interface ButtonsProps {
  items?: ButtonItemProps[];
  layout?: "row" | "column";
  children?: React.ReactNode;
}

export function Buttons({ items, layout = "row", children }: ButtonsProps) {
  return (
    <div
      className={cn(
        "flex flex-wrap gap-2",
        layout === "column" ? "flex-col items-start" : "flex-row items-center",
      )}
    >
      {children ?? (items || []).map((btn, i) => <ButtonItem key={i} {...btn} />)}
    </div>
  );
}
