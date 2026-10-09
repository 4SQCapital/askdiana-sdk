import { useEffect, useRef, useState } from "react";
import { Button, Skeleton } from "askdiana-ui";
import { ConnectionSummary } from "../../components/connection/ConnectionSummary";
import { CredentialForm } from "../../components/connection/CredentialForm";
import { DeploymentCard } from "../../components/connection/DeploymentCard";
import { MethodPanel } from "../../components/connection/MethodPanel";
import { MethodPicker } from "../../components/connection/MethodPicker";
import { Banner } from "../../components/feedback/Banner";
import { ErrorState } from "../../components/feedback/ErrorState";
import { Modal } from "../../components/ui/Modal";
import { useConnectSession } from "../../hooks/useConnectSession";
import { useConnection } from "../../hooks/useErpData";
import { useHostEvent } from "../../hooks/useHostEvent";
import { API, ApiError, postJson } from "../../lib/api";
import { HOST_EVENT, HOST_REQUEST, IN_HOST, postToHost } from "../../lib/host";
import type {
  ConnectOption,
  ConnectionPayload,
  Deployment,
} from "../../types/connection";

const POLL_MS = 3000;
const WAIT_LIMIT_MS = 3 * 60 * 1000;

interface ConnectionDialogProps {
  open: boolean;
  onClose: () => void;
  installId: string;
  refreshKey: number;
  onRetry: () => void;
  inline?: boolean;
}

function currentGroup(status: ConnectionPayload): Deployment | undefined {
  const current = status.options.find((o) => o.method === status.method);
  return current?.deployment ?? status.groups[0]?.id;
}

function connectError(e: unknown): string {
  if (e instanceof ApiError && e.message.includes("connect link")) {
    return "The connect session expired. Please try again.";
  }
  return e instanceof Error ? e.message : "Could not connect.";
}

export function ConnectionDialog({
  open,
  onClose,
  installId,
  refreshKey,
  onRetry,
  inline,
}: ConnectionDialogProps) {
  const [pollKey, setPollKey] = useState(0);
  const { data, error, loading } = useConnection(
    installId,
    refreshKey + pollKey,
  );
  const [changing, setChanging] = useState(false);
  const showForms = !!data && (!data.connected || changing);
  const connectSession = useConnectSession(installId, open && showForms);
  const { session } = connectSession;

  const [group, setGroup] = useState<Deployment | undefined>();
  const [methodByGroup, setMethodByGroup] = useState<
    Partial<Record<Deployment, string>>
  >({});
  const [busyMethod, setBusyMethod] = useState<string | null>(null);
  const [formError, setFormError] = useState<string | null>(null);
  const [waiting, setWaiting] = useState(false);
  const [timedOut, setTimedOut] = useState(false);
  const [confirming, setConfirming] = useState(false);

  useEffect(() => {
    if (data && !group) setGroup(currentGroup(data));
  }, [data, group]);

  const lastState = useRef<string | undefined>(undefined);
  useEffect(() => {
    if (!data) return;
    const state = `${data.connected}:${data.method}`;
    const changed =
      lastState.current !== undefined && lastState.current !== state;
    lastState.current = state;
    if (!changed) return;
    setWaiting(false);
    setChanging(false);
    setConfirming(false);
    setFormError(null);
    onRetry();
  }, [data, onRetry]);

  useEffect(() => {
    if (!waiting) return;
    const poll = setInterval(() => setPollKey((k) => k + 1), POLL_MS);
    const limit = setTimeout(() => {
      setWaiting(false);
      setTimedOut(true);
    }, WAIT_LIMIT_MS);
    return () => {
      clearInterval(poll);
      clearTimeout(limit);
    };
  }, [waiting]);

  useEffect(() => {
    if (open) return;
    setChanging(false);
    setConfirming(false);
    setFormError(null);
    setWaiting(false);
    setTimedOut(false);
  }, [open]);

  useHostEvent(HOST_EVENT.connectionError, (payload) => {
    setWaiting(false);
    setFormError(
      (payload as { message?: string } | undefined)?.message ??
        "AskDiana could not connect.",
    );
  });

  const signIn = () => {
    if (!session) return;
    setFormError(null);
    setTimedOut(false);
    setWaiting(true);
    postToHost(HOST_REQUEST.connectOAuth, { url: session.oauthUrl });
  };

  const submit = async (
    method: string,
    values: Record<string, string>,
  ): Promise<boolean> => {
    if (!session?.nonce) return false;
    setFormError(null);
    setBusyMethod(method);
    try {
      const { callback } = await postJson<{ callback: string }>(API.connect, {
        ...values,
        install_id: installId,
        nonce: session.nonce,
        method,
      });
      postToHost(HOST_REQUEST.connectComplete, { callback });
      setPollKey((k) => k + 1);
      return true;
    } catch (e) {
      setFormError(connectError(e));
      connectSession.renew();
      return false;
    } finally {
      setBusyMethod(null);
    }
  };

  const disconnect = () => {
    if (!confirming) {
      setConfirming(true);
      return;
    }
    setFormError(null);
    postToHost(HOST_REQUEST.disconnect);
  };

  const selected = data?.groups.find((g) => g.id === group) ?? data?.groups[0];
  // With several logins in a group, show one form at a time: the picked one, else the one in use
  const groupOptions = selected?.options ?? [];
  const chosen =
    groupOptions.find((o) => o.method === (selected && methodByGroup[selected.id])) ??
    groupOptions.find((o) => o.method === data?.method) ??
    groupOptions[0];
  const formsDisabled = !IN_HOST || !session || waiting;

  const renderMethod = (option: ConnectOption) => {
    const current = !!data?.connected && option.method === data.method;
    let body;
    if (option.method === "oauth2") {
      body = (
        <Button className="w-full" onClick={signIn} disabled={formsDisabled}>
          {waiting ? "Waiting for the sign-in window…" : option.label}
        </Button>
      );
    } else {
      body = (
        <CredentialForm
          method={option.method}
          inputs={option.inputs}
          disabled={
            formsDisabled ||
            !session?.nonce ||
            (busyMethod !== null && busyMethod !== option.method)
          }
          busy={busyMethod === option.method}
          onSubmit={(values) => submit(option.method, values)}
        />
      );
    }
    return (
      <MethodPanel key={option.method} option={option} current={current}>
        {body}
      </MethodPanel>
    );
  };

  const hasFooter = !!data && (waiting || data.connected);
  const footer = hasFooter && (
    <>
      {waiting && (
        <Button variant="ghost" size="sm" onClick={() => setWaiting(false)}>
          Stop waiting
        </Button>
      )}
      {data.connected && !changing && (
        <>
          <Button
            variant="outline"
            size="sm"
            onClick={disconnect}
            disabled={!IN_HOST}
            className={
              confirming ? "border-destructive text-destructive" : undefined
            }
          >
            {confirming ? "Click again to disconnect" : "Disconnect"}
          </Button>
          <Button
            size="sm"
            onClick={() => setChanging(true)}
            disabled={!IN_HOST}
          >
            Change connection
          </Button>
        </>
      )}
      {data.connected && changing && !waiting && (
        <Button variant="outline" size="sm" onClick={() => setChanging(false)}>
          Cancel
        </Button>
      )}
    </>
  );

  return (
    <Modal
      open={open}
      title="Connection"
      onClose={onClose}
      size="md"
      footer={footer}
      inline={inline}
    >
      {error ? (
        <ErrorState message={error} onRetry={onRetry} />
      ) : !data ? (
        <div className="space-y-3" aria-busy={loading}>
          <Skeleton className="h-14 w-full" />
          <div className="grid grid-cols-2 gap-3">
            <Skeleton className="h-28" />
            <Skeleton className="h-28" />
          </div>
        </div>
      ) : (
        <div className="space-y-4">
          <ConnectionSummary status={data} />
          {formError && <Banner tone="error">{formError}</Banner>}
          {!IN_HOST && (
            <Banner tone="info">
              Open this panel inside AskDiana to connect or disconnect.
            </Banner>
          )}
          {showForms && IN_HOST && connectSession.loading && (
            <p className="text-xs text-muted-foreground" aria-live="polite">
              Preparing a secure connection…
            </p>
          )}
          {showForms && IN_HOST && connectSession.error && (
            <Banner
              tone="warning"
              action={
                <Button
                  size="sm"
                  variant="outline"
                  onClick={connectSession.renew}
                >
                  Try again
                </Button>
              }
            >
              {connectSession.error}
            </Banner>
          )}

          {showForms && (
            <>
              {data.groups.length > 1 && (
                <div className="grid grid-cols-2 gap-3">
                  {data.groups.map((g) => (
                    <DeploymentCard
                      key={g.id}
                      group={g}
                      selected={g.id === selected?.id}
                      onSelect={() => setGroup(g.id)}
                    />
                  ))}
                </div>
              )}
              {selected && groupOptions.length > 1 && chosen && (
                <MethodPicker
                  options={groupOptions}
                  value={chosen.method}
                  onChange={(method) => {
                    setFormError(null);
                    setMethodByGroup((m) => ({ ...m, [selected.id]: method }));
                  }}
                />
              )}
              {chosen && renderMethod(chosen)}
              {waiting && (
                <p className="text-xs text-muted-foreground" aria-live="polite">
                  Finish in the window that opened; this panel updates when
                  you're connected. No window? Your browser may have blocked it:
                  allow pop-ups for AskDiana and try again.
                </p>
              )}
              {timedOut && (
                <Banner tone="warning">
                  Still not connected. Please try again.
                </Banner>
              )}
              <p className="text-center text-[11px] text-muted-foreground">
                Keys and passwords are checked with the system and never shown
                again.
              </p>
            </>
          )}
        </div>
      )}
    </Modal>
  );
}
