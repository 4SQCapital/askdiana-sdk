import React from "react";
import { cn } from "../../lib/cn";

export interface GalleryItem {
  url: string;
  alt?: string;
  caption?: string;
}

export interface GalleryProps {
  items: GalleryItem[];
  columns?: 2 | 3 | 4;
}

const COLS_MAP: Record<number, string> = {
  2: "grid-cols-2",
  3: "grid-cols-2 sm:grid-cols-3",
  4: "grid-cols-2 sm:grid-cols-3 md:grid-cols-4",
};

export function Gallery({ items, columns = 3 }: GalleryProps) {
  return (
    <div className={cn("grid gap-2", COLS_MAP[columns] ?? COLS_MAP[3])}>
      {items.map((item, i) => (
        <figure key={i} className="overflow-hidden rounded-lg">
          <img
            src={item.url}
            alt={item.alt || ""}
            className="h-32 w-full rounded-lg border border-border object-cover"
          />
          {item.caption && (
            <figcaption className="mt-1 truncate text-xs text-muted-foreground">
              {item.caption}
            </figcaption>
          )}
        </figure>
      ))}
    </div>
  );
}
