from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

import requests

from . import http
from .errors import ErpError


@dataclass(frozen=True)
class Session:
    api_base: str
    headers: Mapping[str, str] = field(default_factory=dict)
    params: Mapping[str, str] = field(default_factory=dict)
    cookies: Mapping[str, str] = field(default_factory=dict)
    
    def get(self, path: str, params: Mapping[str, Any] | None = None) -> requests.Response:
        return self.send("GET", path, params)

    def send(self, method: str, path: str, params: Mapping[str, Any] | None = None,
             body: Any = None) -> requests.Response:
        """GET with query params, or POST with a JSON body (a query API such as Sage Intacct's)."""
        extra = {"json": body} if body is not None else {}
        return http.request(method, self.url(path), headers=dict(self.headers),
                            params={**self.params, **(params or {})}, cookies=dict(self.cookies), **extra)

    def url(self, path: str) -> str:
        if not path.lower().startswith(("http://", "https://")):
            return self.api_base + path
        # A server-given next-page link: only followed under the same API base, so the login never leaves it
        base = self.api_base.rstrip("/")
        if not (path.lower().startswith(base.lower()) and path[len(base):len(base) + 1] in ("", "/", "?")):
            raise ErpError(ErpError.VENDOR, "The server's next-page link points outside its API address")
        return path