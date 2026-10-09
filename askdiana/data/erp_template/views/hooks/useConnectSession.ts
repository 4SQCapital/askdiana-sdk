import { useCallback, useEffect, useState } from "react";
import { API } from "../lib/api";
import { HOST_EVENT, HOST_REQUEST, IN_HOST, requestHost } from "../lib/host";

export interface ConnectSession {
  nonce: string | null;
  oauthUrl: string;
}

/** Turn AskDiana's connect link into what the dialog needs. */
function parse(url: string, installId: string): ConnectSession {
  const link = new URL(url);
  const nonce = link.searchParams.get("nonce");
  if (!nonce) return { nonce: null, oauthUrl: url };
  const oauth = new URL(API.connectOAuth, link.origin);
  oauth.search = new URLSearchParams({
    install_id: installId,
    nonce,
  }).toString();
  return { nonce, oauthUrl: oauth.toString() };
}

export function useConnectSession(installId: string, active: boolean) {
  const [session, setSession] = useState<ConnectSession | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    if (!active || !installId || !IN_HOST) return;
    let cancelled = false;
    setLoading(true);
    setError(null);
    requestHost<{ url: string }>(
      HOST_REQUEST.connectSession,
      {},
      HOST_EVENT.connectSession,
    )
      .then(({ url }) => !cancelled && setSession(parse(url, installId)))
      .catch((e: Error) => !cancelled && setError(e.message))
      .finally(() => !cancelled && setLoading(false));
    return () => {
      cancelled = true;
    };
  }, [active, installId, attempt]);

  const renew = useCallback(() => {
    setSession(null);
    setAttempt((n) => n + 1);
  }, []);

  return { session, error, loading, renew };
}
