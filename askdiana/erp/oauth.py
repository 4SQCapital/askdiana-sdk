from __future__ import annotations

import logging
import time
from collections.abc import Mapping
from typing import Any
from urllib.parse import urlencode

import requests

from . import constants as C
from . import http
from .errors import ErpError
from .mapping import get_path
from .pack import OAuthSpec
from .session import Session
from .settings import env_str

logger = logging.getLogger(__name__)


class OAuth2Flow:
    def __init__(self, spec: OAuthSpec, label: str):
        self.spec = spec
        self._label = label
    
    # ------------------------------------------------------------ sign-in

    def auth_url(self, install_id: str, redirect_uri: str) -> str:
        params = {
            "response_type": "code",
            "client_id": self._client_id(),
            "redirect_uri": redirect_uri,
            "scope": self.spec.scope,
            "state": install_id,
            **self.spec.authorize_params,
        }
        return f"{self._default_server()}{self.spec.authorize_path}?{urlencode(params)}"

    def exchange(self, code: str, redirect_uri: str, extra: Mapping[str, str]) -> dict[str, Any]:
        token_data, server = self._exchange_code(code, redirect_uri, extra)
        record = self._token_record(token_data, server)
        record[C.TOKEN_ACCOUNT_LABEL] = self._account_label(record)
        return record

    # ------------------------------------------------------------ using a stored record
    
    @staticmethod
    def is_connected(record: Mapping[str, Any]) -> bool:
        return bool(record.get(C.TOKEN_ACCESS))

    @staticmethod
    def expiring(record: Mapping[str, Any]) -> bool:
        expires_at = record.get(C.TOKEN_EXPIRES_AT)
        return isinstance(expires_at, (int, float)) and expires_at - C.TOKEN_REFRESH_LEEWAY_SECONDS <= time.time()

    def session(self, record: Mapping[str, Any]) -> Session:
        return Session(api_base=record.get(self.spec.api_base_field) or self.spec.api_base_default,
                       headers=self._auth_header(record[C.TOKEN_ACCESS]))

    def refresh(self, record: Mapping[str, Any]) -> dict[str, Any]:
        refresh_token = record.get(C.TOKEN_REFRESH)
        if not refresh_token:
            raise ErpError(ErpError.UNAUTHORIZED, f"{self._label} login expired. Reconnect your account.")
        server = record.get(C.TOKEN_AUTH_SERVER) or self._default_server()
        try:
            response = http.request("POST", server + self.spec.token_path, data={
                "grant_type": C.GRANT_REFRESH_TOKEN,
                "refresh_token": refresh_token,
                "client_id": self._client_id(),
                "client_secret": self._client_secret(),
            })
        except requests.RequestException as exc:
            raise ErpError(ErpError.VENDOR, f"{self._label} login refresh failed: {exc}") from exc
        body = http.json_or_empty(response)
        if not response.ok or not body.get(C.TOKEN_ACCESS):
            raise ErpError(ErpError.UNAUTHORIZED, f"{self._label} login expired. Reconnect your account.")
        return self._token_record(body, server, previous=record)

    def revoke(self, record: Mapping[str, Any]) -> None:
        refresh_token = record.get(C.TOKEN_REFRESH)
        if not (refresh_token and self.spec.revoke_path):
            return
        server = record.get(C.TOKEN_AUTH_SERVER) or self._default_server()
        try:
            http.request("POST", server + self.spec.revoke_path,
                         data={self.spec.revoke_param: refresh_token}, retry=False)
        except requests.RequestException as exc:
            logger.warning("%s token revoke failed: %s", self._label, exc)

    # ------------------------------------------------------------ internals

    def _auth_header(self, access_token: str) -> dict[str, str]:
        return {"Authorization": self.spec.token_header.format(token=access_token)}

    def _client_id(self) -> str:
        return self._required_env(self.spec.client_id_env)

    def _client_secret(self) -> str:
        return self._required_env(self.spec.client_secret_env)

    @staticmethod
    def _required_env(name: str) -> str:
        value = env_str(name)
        if not value:
            raise ErpError(ErpError.CONFIG, f"{name} is not configured for this extension")
        return value

    def _default_server(self) -> str:
        override = env_str(self.spec.auth_server_env) if self.spec.auth_server_env else ""
        return (override or self.spec.auth_server_default).rstrip("/")

    def _candidate_servers(self, extra: Mapping[str, str]) -> list[str]:
        default = self._default_server()
        allowed = {default, *self.spec.auth_servers}
        hinted = (extra.get(self.spec.auth_server_param) or "").rstrip("/") if self.spec.auth_server_param else ""
        if hinted in allowed:
            return [hinted]
        if hinted:
            logger.warning("%s: ignoring unknown auth server hint %r", self._label, hinted)
        return [default] + [s for s in self.spec.auth_servers if s != default]

    def _exchange_code(self, code: str, redirect_uri: str, extra: Mapping[str, str]) -> tuple[dict, str]:
        payload = {
            "grant_type": C.GRANT_AUTHORIZATION_CODE,
            "code": code,
            "client_id": self._client_id(),
            "client_secret": self._client_secret(),
            "redirect_uri": redirect_uri,
        }
        last_error = "no auth server configured"
        for server in self._candidate_servers(extra):
            try:
                response = http.request("POST", server + self.spec.token_path, data=payload, retry=False)
            except requests.RequestException as exc:
                last_error = str(exc)
                continue
            body = http.json_or_empty(response)
            if response.ok and body.get(C.TOKEN_ACCESS):
                return body, server
            last_error = body.get("error") or f"HTTP {response.status_code}"
        raise ErpError(ErpError.UNAUTHORIZED, f"{self._label} sign-in failed: {last_error}")

    def _token_record(self, token_data: Mapping[str, Any], server: str,
                      previous: Mapping[str, Any] | None = None) -> dict[str, Any]:
        record = dict(previous or {})
        record[C.TOKEN_ACCESS] = token_data[C.TOKEN_ACCESS]
        if token_data.get(C.TOKEN_REFRESH):
            record[C.TOKEN_REFRESH] = token_data[C.TOKEN_REFRESH]
        record[self.spec.api_base_field] = (
            token_data.get(self.spec.api_base_field)
            or record.get(self.spec.api_base_field)
            or self.spec.api_base_default
        )
        record[C.TOKEN_AUTH_SERVER] = server
        expires_in = token_data.get(C.TOKEN_EXPIRES_IN)
        if isinstance(expires_in, (int, float)):
            record[C.TOKEN_EXPIRES_AT] = time.time() + expires_in
        return record

    def _account_label(self, record: Mapping[str, Any]) -> str | None:
        info = self.spec.account_info
        if not info:
            return None
        try:
            response = http.request(
                "GET", record[self.spec.api_base_field] + info["path"],
                headers=self._auth_header(record[C.TOKEN_ACCESS]), params=info.get("params"), retry=False,
            )
        except requests.RequestException as exc:
            logger.warning("%s account lookup failed: %s", self._label, exc)
            return None
        return get_path(http.json_or_empty(response), info["label_path"]) if response.ok else None
