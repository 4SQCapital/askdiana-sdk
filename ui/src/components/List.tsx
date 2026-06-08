import React, { isValidElement } from "react";

export interface ItemProps {
  children: React.ReactNode;
}

/** A single row inside <List>. Purely structural — renders as <li>. */
export function Item({ children }: ItemProps) {
  return <>{children}</>;
}
Item.displayName = "List.Item";

export interface ListProps {
  /** Simple string items — used when you don't need <Item> children. */
  items?: string[];
  ordered?: boolean;
  /** <Item>…</Item> children — takes precedence over `items` when present. */
  children?: React.ReactNode;
}

export function List({ items, ordered = false, children }: ListProps) {
  const Tag = ordered ? "ol" : "ul";

  if (children) {
    const rows = React.Children.toArray(children).filter(isValidElement);
    return (
      <Tag>
        {rows.map((child, i) => (
          <li key={i}>
            {(child as React.ReactElement<ItemProps>).props.children}
          </li>
        ))}
      </Tag>
    );
  }

  return (
    <Tag>
      {(items || []).map((it, i) => (
        <li key={i}>{it}</li>
      ))}
    </Tag>
  );
}
