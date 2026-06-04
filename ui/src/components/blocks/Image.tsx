import React from "react";

interface ImageProps {
  url: string;
  alt?: string;
  caption?: string;
}

export function Image({ url, alt, caption }: ImageProps) {
  return (
    <figure>
      <img src={url} alt={alt || ""} className="max-w-full rounded-md" />
      {caption && (
        <figcaption className="mt-1 text-xs text-muted-foreground">
          {caption}
        </figcaption>
      )}
    </figure>
  );
}
