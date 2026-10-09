import { useEffect, type ReactNode } from "react";
import { IconButton } from "./IconButton";
import { CloseIcon } from "./icons";

const SIZE_CLASS = { md: "max-w-lg", xl: "max-w-5xl" } as const;

interface ModalProps {
  open: boolean;
  title: string;
  onClose: () => void;
  actions?: ReactNode;
  footer?: ReactNode;
  size?: keyof typeof SIZE_CLASS;
  /** Render the dialog itself without a backdrop: the page inside AskDiana's centered modal. */
  inline?: boolean;
  children: ReactNode;
}

/** Full-width dialog over the panel. Closes on Escape or a click on the backdrop. */
export function Modal({
  open,
  title,
  onClose,
  actions,
  footer,
  size = "xl",
  inline = false,
  children,
}: ModalProps) {
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  if (!open) return null;
  if (inline) {
    return (
      <div role="dialog" aria-label={title} className="flex min-h-full flex-col bg-card text-card-foreground">
        <div className="sticky top-0 z-10 flex items-center justify-between gap-3 border-b bg-card px-4 py-3">
          <h2 className="truncate text-sm font-semibold">{title}</h2>
          <div className="flex items-center gap-2">
            {actions}
            <IconButton label="Close" onClick={onClose}>
              <CloseIcon />
            </IconButton>
          </div>
        </div>
        <div className="flex-1 p-4">{children}</div>
        {footer && (
          <div className="sticky bottom-0 flex flex-wrap items-center justify-end gap-2 border-t bg-card px-4 py-3">
            {footer}
          </div>
        )}
      </div>
    );
  }
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
      onClick={onClose}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-label={title}
        className={`flex max-h-full w-full ${SIZE_CLASS[size]} flex-col rounded-xl border bg-card text-card-foreground shadow-xl`}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between gap-3 border-b px-4 py-3">
          <h2 className="truncate text-sm font-semibold">{title}</h2>
          <div className="flex items-center gap-2">
            {actions}
            <IconButton label="Close" onClick={onClose}>
              <CloseIcon />
            </IconButton>
          </div>
        </div>
        <div className="overflow-auto p-4">{children}</div>
        {footer && (
          <div className="flex flex-wrap items-center justify-end gap-2 border-t px-4 py-3">
            {footer}
          </div>
        )}
      </div>
    </div>
  );
}
