import { useCallback, useEffect, useRef, useState } from "react";
import { cn } from "askdiana-ui";
import { ChevronLeftIcon, ChevronRightIcon } from "../ui/icons";
import type { TabRef } from "../../types/dashboard";

const SCROLL_STEP = 240;

interface ScrollTabsProps {
  tabs: TabRef[];
  activeId: string;
  onSelect: (id: string) => void;
  ariaLabel: string;
}

/** A row of tab chips that scrolls sideways with arrow buttons when it doesn't fit (like the Odoo KPI strip). */
export function ScrollTabs({
  tabs,
  activeId,
  onSelect,
  ariaLabel,
}: ScrollTabsProps) {
  const rowRef = useRef<HTMLDivElement>(null);
  const [edges, setEdges] = useState({ left: false, right: false });

  const measure = useCallback(() => {
    const el = rowRef.current;
    if (!el) return;
    setEdges({
      left: el.scrollLeft > 0,
      right: el.scrollLeft < el.scrollWidth - el.clientWidth - 1,
    });
  }, []);

  useEffect(() => {
    measure();
    const el = rowRef.current;
    if (!el) return;
    el.addEventListener("scroll", measure, { passive: true });
    const observer = new ResizeObserver(measure);
    observer.observe(el);
    return () => {
      el.removeEventListener("scroll", measure);
      observer.disconnect();
    };
  }, [measure, tabs.length]);

  useEffect(() => {
    rowRef.current
      ?.querySelector<HTMLElement>(`[data-tab-id="${CSS.escape(activeId)}"]`)
      ?.scrollIntoView({
        behavior: "smooth",
        inline: "nearest",
        block: "nearest",
      });
  }, [activeId]);

  const scroll = (direction: -1 | 1) =>
    rowRef.current?.scrollBy({
      left: direction * SCROLL_STEP,
      behavior: "smooth",
    });

  return (
    <div className="relative">
      {edges.left && <EdgeButton side="left" onClick={() => scroll(-1)} />}
      <div
        ref={rowRef}
        role="tablist"
        aria-label={ariaLabel}
        className="erp-tabs flex gap-2 overflow-x-auto scroll-smooth py-1 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden"
      >
        {tabs.map((tab) => {
          const active = tab.id === activeId;
          return (
            <button
              key={tab.id}
              type="button"
              role="tab"
              data-tab-id={tab.id}
              aria-selected={active}
              data-active={active}
              onClick={() => onSelect(tab.id)}
              className={cn(
                "erp-tab shrink-0 rounded-full border px-3.5 py-1.5 text-sm font-medium transition-colors",
                "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
                active
                  ? "border-primary bg-primary text-primary-foreground shadow-sm"
                  : "border-border bg-background text-muted-foreground hover:bg-accent hover:text-foreground",
              )}
            >
              {tab.label}
            </button>
          );
        })}
      </div>
      {edges.right && <EdgeButton side="right" onClick={() => scroll(1)} />}
    </div>
  );
}

function EdgeButton({
  side,
  onClick,
}: {
  side: "left" | "right";
  onClick: () => void;
}) {
  const left = side === "left";
  return (
    <div
      className={cn(
        "absolute inset-y-0 z-10 flex items-center",
        left ? "left-0 bg-gradient-to-r pr-6" : "right-0 bg-gradient-to-l pl-6",
        "from-background via-background/90 to-transparent",
      )}
    >
      <button
        type="button"
        aria-label={left ? "Scroll tabs left" : "Scroll tabs right"}
        onClick={onClick}
        className="flex h-7 w-7 items-center justify-center rounded-full border bg-background shadow-sm hover:bg-accent"
      >
        {left ? <ChevronLeftIcon /> : <ChevronRightIcon />}
      </button>
    </div>
  );
}
