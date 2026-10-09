import { useEffect, useRef } from "react";
import { onHostMessage } from "../lib/host";

export function useHostEvent(
  type: string,
  handler: (payload: unknown) => void,
) {
  const latest = useRef(handler);
  latest.current = handler;
  useEffect(
    () => onHostMessage(type, (payload) => latest.current(payload)),
    [type],
  );
}
