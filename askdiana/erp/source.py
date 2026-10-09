from __future__ import annotations

import logging
import threading
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from datetime import date
from typing import Any

from . import constants as C
from .cache import TTLCache
from .connector import ErpConnector
from .errors import ErpError
from .mapping import date_token, get_path, map_record, placeholders, render
from .pack import EntitySpec, Pack, PagingSpec
from .settings import env_flag, env_int
from .transport import DirectTransport

logger = logging.getLogger(__name__)

DemoProvider = Callable[[], Mapping[str, list[dict]]]
Getter = Callable[[str, Mapping[str, Any]], Any]


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
        def send(path: str, params: Mapping[str, Any], body: Any = None):
            if body is None:
                return self._transport.get(install_id, path, params)
            return self._transport.request(install_id, C.METHOD_POST, path, params, body)

        raw, truncated = fetch_raw(self._pack, entity, send)
        if truncated:
            logger.warning("%s %s truncated at %d pages (%d records)",
                        self._pack.label, entity.name, self._pack.paging.max_pages, len(raw))
        return self._mapped(entity, raw, truncated=truncated)

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


def fetch_raw(pack: Pack, entity: EntitySpec, get: Getter, *, max_pages: int | None = None) -> tuple[list[dict], bool]:
    paging = pack.paging
    fixed: dict[str, Any] = dict(entity.params)
    if paging.fields_param:
        fixed[paging.fields_param] = entity.source_fields
    raw: list[dict] = []
    page, token, link = 1, None, None
    for _ in range(max_pages or paging.max_pages):
        # A next link already holds every param; the session checks it stays on the API's own address
        if link:
            response = get(link, {})
        elif entity.method == C.METHOD_POST:
            response = get(entity.path, _page_params(paging, fixed, page, token), _page_body(paging, entity, page))
        else:
            response = get(entity.path, _page_params(paging, fixed, page, token))
        if paging.empty_status is not None and response.status_code == paging.empty_status:
            return raw, False
        body = response.json()
        records = get_path(body, entity.records_path) or []
        raw.extend(records)
        if paging.next_link_path:
            link = get_path(body, paging.next_link_path)
            if not link:
                return raw, False
            continue
        if not _has_more(paging, body, len(records)):
            return raw, False
        token = get_path(body, paging.next_token_path) if paging.next_token_path else None
        page += 1
    return raw, True


def _paging_values(paging: PagingSpec, page: int) -> dict[str, int]:
    offset = (page - 1) * paging.page_size
    return {"page": page, "size": paging.page_size, "offset": offset, "position": offset + 1}


def _page_body(paging: PagingSpec, entity: EntitySpec, page: int) -> dict[str, Any]:
    """The JSON query body for one page: paging placeholders and date tokens filled, the field list added."""
    values, today = _paging_values(paging, page), date.today()

    def fill(value: Any) -> Any:
        if isinstance(value, Mapping):
            return {key: fill(item) for key, item in value.items()}
        if isinstance(value, list):
            return [fill(item) for item in value]
        if not isinstance(value, str):
            return value
        names = placeholders(value)
        if len(names) == 1 and value == "{" + names[0] + "}" and names[0] in values:
            return values[names[0]]  # a bare "{size}" stays a number
        if set(names) & C.PAGING_PLACEHOLDERS:
            return render(value, values)
        return date_token(value, today)

    body = fill(entity.body)
    if paging.fields_body:
        body[paging.fields_body] = entity.source_paths
    return body


def _page_params(paging: PagingSpec, fixed: Mapping[str, Any], page: int, token: Any) -> dict[str, Any]:
    values = _paging_values(paging, page)
    params = {key: render(value, values) if set(placeholders(value)) & C.PAGING_PLACEHOLDERS else value
              for key, value in fixed.items()}
    if paging.size_param:
        params[paging.size_param] = paging.page_size
    if token and paging.token_param:
        params[paging.token_param] = token
    elif paging.page_param:
        params[paging.page_param] = page
    return params


def _has_more(paging: PagingSpec, body: Mapping[str, Any], count: int) -> bool:
    if paging.stop_on_short_page and count < paging.page_size:
        return False
    if paging.more_path:
        return bool(get_path(body, paging.more_path))
    return count > 0

