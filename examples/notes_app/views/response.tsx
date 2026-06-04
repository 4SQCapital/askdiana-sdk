import React from "react";
import { Response, Text, List, Alert, type InitData } from "askdiana-ui";

export default function NotesResponse({
  init,
}: {
  init: InitData;
  installId: string;
}) {
  // If the backend sent a rich_response payload, render it dynamically:
  const serverBlocks = init.params?.blocks as any[] | undefined;
  if (serverBlocks) return <Response blocks={serverBlocks} />;

  // Otherwise hand-author a layout with tags:
  return (
    <Response>
      <Text>Here are your latest notes:</Text>
      <List items={["Buy milk", "Call Alex", "Ship the SDK"]} />
      <Alert variant="success">All synced.</Alert>
    </Response>
  );
}
