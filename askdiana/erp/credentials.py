from __future__ import annotations

import base64
import ipaddress
import socket
from collections.abc import Mapping
from typing import Any
from urllib.parse import urlparse

import requests

from . import constants as C
from . import http
from .cache import TTLCache
from .errors import ErpError
from .mapping import get_path, placeholders, render
from .pack import CredentialSpec
from .session import Session
from .settings import env_flag


def check_url(url: str) -> str:
    insecure_ok = env_flag(C.ENV_ALLOW_INSECURE_URLS, C.DEFAULT_ALLOW_INSECURE_URLS)
    schemes = C.DEV_URL_SCHEMES if insecure_ok else C.SECURE_URL_SCHEMES
    parsed = urlparse(url)
    if parsed.scheme not in schemes or not parsed.hostname:
        raise ErpError(ErpError.INVALID, "Enter the full server address, starting with https://")
    if insecure_ok:
        return url
    try:
        addresses = {info[4][0] for info in socket.getaddrinfo(parsed.hostname, parsed.port or C.DEFAULT_HTTPS_PORT)}
    except socket.gaierror:
        raise ErpError(ErpError.INVALID, f"Can't find the server '{parsed.hostname}'. Check the address.") from None
    if any(not ipaddress.ip_address(address.split("%")[0]).is_global for address in addresses):
        raise ErpError(ErpError.INVALID, f"'{parsed.hostname}' is on a private network, so it can't be reached "
                                         "from the cloud. On-prem systems connect through the AskDiana proxy.")
    return url


def _render_all(templates: Mapping[str, str], values: Mapping[str, Any]) -> dict[str, str]:
    rendered = {}
    for key, template in templates.items():
        names = placeholders(template)
        if names and not any(values.get(name) for name in names):
            continue
        rendered[key] = render(template, values)
    return rendered


class CredentialFlow:
    def __init__(self, spec: CredentialSpec, label: str):
        self.spec = spec
        self._label = label
        self._sessions = TTLCache(spec.login.ttl_seconds) if spec.login else None

    # ------------------------------------------------------------ connect

    def clean(self, form: Mapping[str, Any]) -> dict[str, str]:
        values: dict[str, str] = {}
        missing: list[str] = []
        for item in self.spec.inputs:
            value = str(form.get(item.name) or item.default or "").strip()
            if value and item.kind == C.INPUT_URL:
                value = check_url(value.rstrip("/"))
            if item.required and not value:
                missing.append(item.label)
            values[item.name] = value
        if missing:
            raise ErpError(ErpError.INVALID, "Please fill in: " + ", ".join(missing))
        return values

    def verify(self, install_id: str, values: Mapping[str, str]) -> None:
        try:
            response = self.session(install_id, values).get(self.spec.test_path)
        except requests.RequestException as exc:
            raise ErpError(ErpError.VENDOR, f"{self._label} could not be reached: {exc}") from exc
        if response.status_code in C.AUTH_REJECTED_STATUSES:
            raise ErpError(ErpError.UNAUTHORIZED, f"{self._label} rejected these details. Check them and try again.",
                           vendor_status=response.status_code)
        if not response.ok:
            raise ErpError(ErpError.VENDOR, f"{self._label} returned HTTP {response.status_code} to the test request.",
                           vendor_status=response.status_code)

    def account_label(self, values: Mapping[str, str]) -> str | None:
        return render(self.spec.account_label, values) if self.spec.account_label else None

    # ------------------------------------------------------------ every request

    def session(self, install_id: str, values: Mapping[str, str], *, force_refresh: bool = False) -> Session:
        context: dict[str, Any] = dict(values)
        if self.spec.login:
            context[C.SESSION_PLACEHOLDER] = self._login(install_id, values, force_refresh=force_refresh)
        headers = _render_all(self.spec.headers, context)
        if self.spec.method == C.AUTH_BASIC:
            pair = f"{values[self.spec.username]}:{values[self.spec.password]}".encode()
            headers["Authorization"] = "Basic " + base64.b64encode(pair).decode("ascii")
        return Session(
            api_base=render(self.spec.api_base, values),
            headers=headers,
            params=_render_all(self.spec.query, context),
            cookies=_render_all(self.spec.cookies, context),
        )

    def forget(self, install_id: str) -> None:
        if self._sessions is not None:
            self._sessions.invalidate_where(lambda key: key == install_id)

    def _login(self, install_id: str, values: Mapping[str, str], *, force_refresh: bool) -> str:
        if not force_refresh:
            hit, session = self._sessions.get(install_id)
            if hit:
                return session
        login = self.spec.login
        body = {key: render(value, values) if isinstance(value, str) else value for key, value in login.body.items()}
        try:
            response = http.request("POST", render(self.spec.api_base, values) + login.path, json=body, retry=False)
        except requests.RequestException as exc:
            raise ErpError(ErpError.VENDOR, f"{self._label} could not be reached: {exc}") from exc
        if not response.ok:
            raise ErpError(ErpError.UNAUTHORIZED, f"{self._label} rejected the login. Reconnect with the correct details.",
                           vendor_status=response.status_code)
        if login.session_from == C.SESSION_FROM_COOKIE:
            session = response.cookies.get(login.session_key)
        else:
            session = get_path(http.json_or_empty(response), login.session_key)
        if not session:
            raise ErpError(ErpError.VENDOR, f"{self._label} login returned no session ('{login.session_key}').")
        self._sessions.set(install_id, str(session))
        return str(session)
