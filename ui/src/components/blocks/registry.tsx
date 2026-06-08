import React from "react";
import { Text } from "./Text";
import { Alert } from "./Alert";
import { List } from "./List";
import { Card } from "./Card";
import { Code } from "./Code";
import { Image } from "./Image";
import { Table } from "./Table";
import { Divider } from "./Divider";

export type BlockRenderer = (block: any, key: React.Key) => React.ReactNode;
const registry = new Map<string, BlockRenderer>();
export function registerBlock(type: string, renderer: BlockRenderer) {
  registry.set(type, renderer);
}
export function getRenderer(type: string) {
  return registry.get(type);
}

registerBlock("text", (b, k) => <Text key={k} content={b.content} />);
registerBlock("alert", (b, k) => (
  <Alert key={k} variant={b.variant} content={b.content ?? b.message} />
));
registerBlock("list", (b, k) => {
  const items = (b.items || []).map((it: string, i: number) => <li key={i}>{it}</li>);
  return b.ordered ? <ol key={k}>{items}</ol> : <ul key={k}>{items}</ul>;
});
registerBlock("card", (b, k) => (
  <Card key={k} title={b.title} body={b.body} accent={b.accent} />
));
registerBlock("code", (b, k) => (
  <Code key={k} content={b.content} language={b.language} />
));
registerBlock("image", (b, k) => (
  <Image key={k} url={b.url} alt={b.alt} caption={b.caption} />
));
registerBlock("table", (b, k) => (
  <Table key={k} headers={b.headers} rows={b.rows} />
));
registerBlock("divider", (_b, k) => <Divider key={k} />);
