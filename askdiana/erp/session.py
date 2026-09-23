from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

import requests

from . import http


@dataclass(frozen=True)
class Session:
    api_base: str
    headers: Mapping[str, str] = field(default_factory=dict)
    params: Mapping[str, str] = field(default_factory=dict)
    cookies: Mapping[str, str] = field(default_factory=dict)
    
    def get(self, path: str, params: Mapping[str, Any] | None = None) -> requests.Response:
        return http.request("GET", self.api_base + path, headers=dict(self.headers),
                            params={**self.params, **(params or {})}, cookies=dict(self.cookies))