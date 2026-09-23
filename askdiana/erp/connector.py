from __future__ import annotations

import secrets
import threading
import time
from collections.abc import Callable, Mapping
from typing import Any
from urllib.parse import urlencode

from askdiana import ConnectorService

from . import constants as C
from .credentials import CredentialFlow
from .errors import ErpError
from .oauth import OAuth2Flow
from .pack import Pack
from .session import Session
from .settings import env_str


class ErpConnector(ConnectorService):
    def __init__(self, client, pack: Pack):
        super().__init__(client)
        self.pack = pack
        self.source_type = self.provider_name = pack.provider
        self.oauth = OAuth2Flow(pack.auth.oauth2, pack.label) if pack.auth.oauth2 else None
        self.credential_flows = {m: CredentialFlow(spec, pack.label) for m, spec in pack.auth.credentials.items()}
        self.on_tokens_changed: list[Callable[[str], None]] = []
        self._locks: dict[str, threading.Lock] = {}
        self._locks_guard = threading.Lock()

    # ------------------------------------------------------------ ConnectorService API (/api/auth/*)

    def get_auth_url(self, install_id: str, redirect_uri: str) -> str:
        if self.pack.auth.methods == (C.AUTH_OAUTH2,):
            return self.oauth.auth_url(install_id, redirect_uri)
        nonce = self._issue_nonce(install_id, redirect_uri)
        return f"{self._public_url()}{C.CONNECT_PAGE_PATH}?{urlencode({'install_id': install_id, 'nonce': nonce})}"

    def handle_auth_callback(self, install_id: str, code: str, redirect_uri: str,
                             extra: Mapping[str, str] | None = None) -> dict:
        if code == C.CONNECTED_CODE:
            status = self.get_auth_status(install_id)
            if not status["connected"]:
                raise ErpError(ErpError.NOT_CONNECTED, f"{self.pack.label} was not connected. Try again.")
            return status
        if self.oauth is None:
            raise ErpError(ErpError.CONFIG, f"{self.pack.label} does not use OAuth sign-in")
        record = self.oauth.exchange(code, redirect_uri, extra or {})
        record[C.TOKEN_AUTH_METHOD] = C.AUTH_OAUTH2
        self._save(install_id, record)
        return {"connected": True, "account_email": record.get(C.TOKEN_ACCOUNT_LABEL)}

    def get_auth_status(self, install_id: str) -> dict:
        record = self._record(install_id)
        connected = self._is_connected(record)
        return {
            "connected": connected,
            "account_email": record.get(C.TOKEN_ACCOUNT_LABEL) if connected else None,
            "auth_method": self._method(record) if connected else None,
        }

    def disconnect(self, install_id: str) -> dict:
        record = self._record(install_id)
        method = self._method(record)
        if method == C.AUTH_OAUTH2 and self.oauth:
            self.oauth.revoke(record)
        elif method in self.credential_flows:
            self.credential_flows[method].forget(install_id)
        self.clear_tokens(install_id)
        self._changed(install_id)
        return {"disconnected": True}

    # ------------------------------------------------------------ used by the transport and data source

    def is_connected(self, install_id: str) -> bool:
        return self._is_connected(self._record(install_id))

    def session(self, install_id: str, *, force_refresh: bool = False) -> Session | None:
        record = self._record(install_id)
        if not self._is_connected(record):
            return None
        method = self._method(record)
        if method == C.AUTH_OAUTH2 and self.oauth:
            if force_refresh or self.oauth.expiring(record):
                record = self._refresh_oauth(install_id, record)
            return self.oauth.session(record)
        flow = self.credential_flows.get(method)
        if flow is None:
            raise ErpError(ErpError.UNAUTHORIZED,
                           f"{self.pack.label} no longer supports '{method}' sign-in. Reconnect your account.")
        return flow.session(install_id, record[C.TOKEN_CREDENTIALS], force_refresh=force_refresh)

    # ------------------------------------------------------------ connect page (§14)

    def check_nonce(self, install_id: str, nonce: str) -> str:
        stored = self._nonce_record(install_id)
        valid = (
            bool(nonce)
            and secrets.compare_digest(str(stored.get("nonce", "")).encode(), nonce.encode())
            and stored.get("expires_at", 0) > time.time()
        )
        if not valid:
            raise ErpError(ErpError.UNAUTHORIZED,
                           "This connect link has expired. Open it again from the Marketplace card.")
        return stored["redirect_uri"]

    def connect_with_credentials(self, install_id: str, nonce: str, method: str,
                                 form: Mapping[str, Any]) -> str:
        redirect_uri = self.check_nonce(install_id, nonce)
        flow = self.credential_flows.get(method)
        if flow is None:
            raise ErpError(ErpError.INVALID, f"Unknown sign-in method '{method}'")
        values = flow.clean(form)
        flow.forget(install_id)
        try:
            flow.verify(install_id, values)
        except ErpError:
            flow.forget(install_id)
            raise
        self._save(install_id, {
            C.TOKEN_AUTH_METHOD: method,
            C.TOKEN_CREDENTIALS: values,
            C.TOKEN_ACCOUNT_LABEL: flow.account_label(values),
        })
        self._delete_nonce(install_id)
        separator = "&" if "?" in redirect_uri else "?"
        return f"{redirect_uri}{separator}{urlencode({'code': C.CONNECTED_CODE, 'state': install_id})}"

    # ------------------------------------------------------------ internals

    def _record(self, install_id: str | None) -> dict[str, Any]:
        return (self.get_tokens(install_id) or {}) if install_id else {}

    @staticmethod
    def _method(record: Mapping[str, Any]) -> str:
        return record.get(C.TOKEN_AUTH_METHOD) or C.AUTH_OAUTH2

    def _is_connected(self, record: Mapping[str, Any]) -> bool:
        if self._method(record) in C.CREDENTIAL_METHODS:
            return bool(record.get(C.TOKEN_CREDENTIALS))
        return OAuth2Flow.is_connected(record)

    def _save(self, install_id: str, record: dict[str, Any]) -> None:
        self.store_tokens(install_id, record)
        self._changed(install_id)

    def _public_url(self) -> str:
        url = env_str(C.ENV_PUBLIC_URL).rstrip("/")
        if not url:
            raise ErpError(ErpError.CONFIG, f"{C.ENV_PUBLIC_URL} is not set. The connect page is served by this "
                                            "extension, so the browser needs its public address.")
        return url

    def _issue_nonce(self, install_id: str, redirect_uri: str) -> str:
        nonce = secrets.token_urlsafe(C.CONNECT_NONCE_BYTES)
        self.client.set_data(install_id, C.CONNECT_NAMESPACE, C.CONNECT_NONCE_KEY, {
            "nonce": nonce,
            "redirect_uri": redirect_uri,
            "expires_at": time.time() + C.CONNECT_NONCE_TTL_SECONDS,
        })
        return nonce

    def _nonce_record(self, install_id: str) -> dict[str, Any]:
        if not install_id:
            return {}
        try:
            return self.client.get_data(install_id, C.CONNECT_NAMESPACE, C.CONNECT_NONCE_KEY) \
                .get("data", {}).get("value") or {}
        except Exception:
            return {}

    def _delete_nonce(self, install_id: str) -> None:
        self.client.delete_data(install_id, C.CONNECT_NAMESPACE, C.CONNECT_NONCE_KEY)

    def _lock_for(self, install_id: str) -> threading.Lock:
        with self._locks_guard:
            return self._locks.setdefault(install_id, threading.Lock())

    def _refresh_oauth(self, install_id: str, seen: Mapping[str, Any]) -> dict[str, Any]:
        with self._lock_for(install_id):
            latest = self._record(install_id) or dict(seen)
            if latest.get(C.TOKEN_ACCESS) != seen.get(C.TOKEN_ACCESS) and not self.oauth.expiring(latest):
                return latest
            updated = self.oauth.refresh(latest)
            self.store_tokens(install_id, updated)
            return updated

    def _changed(self, install_id: str) -> None:
        for callback in self.on_tokens_changed:
            callback(install_id)
