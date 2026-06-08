import React from "react";
import { Response, Text, List, type InitData } from "askdiana-ui";

export default function NotesApp({
  init,
}: {
  init: InitData;
  installId: string;
}) {
  return (
    <Response>
      <Text>Your notes</Text>
      <List items={["dsafadsf", "asdfsfafas"]} />
    </Response>
  );
}
