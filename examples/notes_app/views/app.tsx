import React from "react";
import { App, Text, List, Item, type InitData } from "askdiana-ui";

export default function NotesApp({
  init,
}: {
  init: InitData;
  installId: string;
}) {
  return (
    <App title="Your notes">
      <Text>Here's what's on your list:</Text>
      <List>
        <Item>Buy milk</Item>
        <Item>Call Alex</Item>
        <Item>Ship the SDK</Item>
      </List>
    </App>
  );
}
