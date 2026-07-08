import React from "react";
import { Response, Text, List, Alert, type InitData } from "askdiana-ui";

export default function NotesResponse({
  init,
}: {
  init: InitData;
  installId: string;
}) {
  // If the host sent the chat reply, render it dynamically. The host passes
  // init.params = { blocks, content, message_id }: `blocks` when the reply
  // was a rich_response, `content` (the raw reply string) always.
  const serverBlocks = init.params?.blocks as any[] | undefined;
  if (serverBlocks) return <Response blocks={serverBlocks} />;
  const content = init.params?.content as string | undefined;
  if (content) return <Response content={content} />;

  // Otherwise hand-author a layout with tags:
  return (
    <Response>
      <Text>Here are your latest notes:</Text>
      <List items={["dsafadsf", "asdfsfafas"]} />
      <Alert variant="success">All synced.</Alert>
    </Response>
  );
}
