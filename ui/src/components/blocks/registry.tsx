import React from "react";
import { Text } from "./Text";
import { Alert } from "./Alert";
import { List } from "./List";
import { Card } from "./Card";
import { Code } from "./Code";
import { Image } from "./Image";
import { Table } from "./Table";
import { Divider } from "./Divider";
import { Embed } from "./Embed";
import { Buttons } from "./Buttons";
import { Gallery } from "./Gallery";
import { Stat } from "./Stat";
import { Badge } from "./Badge";
import { Progress } from "./Progress";
import { Timeline } from "./Timeline";

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
registerBlock("embed", (b, k) => (
  <Embed
    key={k}
    url={b.url}
    title={b.title}
    description={b.description}
    aspectRatio={b.aspect_ratio}
    allowFullscreen={b.allow_fullscreen}
  />
));
registerBlock("buttons", (b, k) => (
  <Buttons key={k} items={b.items ?? b.buttons} layout={b.layout} />
));
registerBlock("gallery", (b, k) => (
  <Gallery key={k} items={b.items} columns={b.columns} />
));
registerBlock("stat", (b, k) => (
  <Stat key={k} label={b.label} value={b.value} delta={b.delta} trend={b.trend} />
));
registerBlock("badge", (b, k) => (
  <Badge key={k} content={b.content ?? b.label} variant={b.variant} />
));
registerBlock("progress", (b, k) => (
  <Progress key={k} label={b.label} value={b.value} max={b.max} variant={b.variant} />
));
registerBlock("timeline", (b, k) => <Timeline key={k} items={b.items} />);
