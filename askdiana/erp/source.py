from __future__ import annotations

import logging
import threading
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from typing import Any

from . import constants as C
from .cache import TTLCache
from .connector import ErpConnector
from .errors import ErpError
from .mapping import get_path, map_record
from .pack import EntitySpec, Pack
from .settings import env_flag, env_int
from .transport import DirectTransport

logger = logging.getLogger(__name__)

DemoProvider = Callable[[], Mapping[str, list[dict]]]


@dataclass(frozen=True)
class FetchResult:
    rows: list[dict]
    truncated: bool = False


class DataSource:
    def __init__(self, pack: Pack, connector: ErpConnector, transport: DirectTransport,
                *, demo_provider: DemoProvider | None = None):
        self._pack = pack
        self._connector = connector
        self._transport = transport
        self._cache = TTLCache(env_int(C.ENV_CACHE_TTL_SECONDS, C.DEFAULT_CACHE_TTL_SECONDS))
        self._demo_provider = demo_provider
        self._demo_enabled = demo_provider is not None and env_flag(
            C.ENV_DEMO_WHEN_DISCONNECTED, C.DEFAULT_DEMO_WHEN_DISCONNECTED)
        self._demo: dict[str, list[dict]] | None = None
        self._demo_lock = threading.Lock()
        connector.on_tokens_changed.append(self.invalidate)

    # ------------------------------------------------------------ public

    def mode(self, install_id: str | None) -> str:
        if install_id and self._connector.is_connected(install_id):
            return C.MODE_LIVE
        return C.MODE_DEMO if self._demo_enabled else C.MODE_DISCONNECTED

    def fetch(self, install_id: str | None, entity_name: str) -> FetchResult:
        entity = self._pack.entity(entity_name)
        mode = self.mode(install_id)
        if mode == C.MODE_DEMO:
            return FetchResult(self._demo_rows(entity))
        if mode == C.MODE_DISCONNECTED:
            raise ErpError(ErpError.NOT_CONNECTED,
                        f"{self._pack.label} is not connected. Connect your account from the Marketplace card.")
        key = (install_id, entity.name)
        hit, cached = self._cache.get(key)
        if hit:
            return cached
        result = self._fetch_live(install_id, entity)
        self._cache.set(key, result)
        return result

    def fetch_many(self, install_id: str | None, entity_names: Iterable[str]) -> tuple[dict[str, list[dict]], tuple[str, ...]]:
        data, truncated = {}, []
        for name in dict.fromkeys(entity_names):
            result = self.fetch(install_id, name)
            data[name] = result.rows
            if result.truncated:
                truncated.append(name)
        return data, tuple(truncated)

    def invalidate(self, install_id: str) -> None:
        self._cache.invalidate_where(lambda key: key[0] == install_id)

    # ------------------------------------------------------------ live

    def _fetch_live(self, install_id: str, entity: EntitySpec) -> FetchResult:
        paging = self._pack.paging
        params: dict[str, Any] = {paging.size_param: paging.page_size, paging.page_param: 1}
        if paging.fields_param:
            params[paging.fields_param] = entity.source_fields

        raw: list[dict] = []
        for _ in range(paging.max_pages):
            response = self._transport.get(install_id, entity.path, params)
            if paging.empty_status is not None and response.status_code == paging.empty_status:
                return self._mapped(entity, raw)
            body = response.json()
            raw.extend(get_path(body, entity.records_path) or [])
            if not get_path(body, paging.more_path):
                return self._mapped(entity, raw)
            self._advance(params, body)

        logger.warning("%s %s truncated at %d pages (%d records)",
                    self._pack.label, entity.name, paging.max_pages, len(raw))
        return self._mapped(entity, raw, truncated=True)

    def _advance(self, params: dict[str, Any], body: Mapping[str, Any]) -> None:
        paging = self._pack.paging
        token = get_path(body, paging.next_token_path) if paging.next_token_path else None
        if token and paging.token_param:
            params.pop(paging.page_param, None)
            params[paging.token_param] = token
        else:
            params[paging.page_param] = int(params.get(paging.page_param, 1)) + 1

    @staticmethod
    def _mapped(entity: EntitySpec, raw: list[dict], *, truncated: bool = False) -> FetchResult:
        return FetchResult([map_record(entity, record) for record in raw], truncated)

    # ------------------------------------------------------------ demo

    def _demo_rows(self, entity: EntitySpec) -> list[dict]:
        with self._demo_lock:
            if self._demo is None:
                raw = self._demo_provider() if self._demo_provider else {}
                self._demo = {name: [map_record(self._pack.entities[name], r) for r in records]
                            for name, records in raw.items() if name in self._pack.entities}
        return self._demo.get(entity.name, [])
