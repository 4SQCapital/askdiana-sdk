from __future__ import annotations

import string
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .pack import EntitySpec

_EMPTY = (None, "")


def get_path(obj: Any, path: str | None) -> Any:
    if not path:
        return None
    current = obj
    for part in path.split("."):
        if isinstance(current, Mapping):
            current = current.get(part)
        elif isinstance(current, list) and part.isdigit() and int(part) < len(current):
            current = current[int(part)]
        else:
            return None
        if current is None:
            return None
    return current


def map_record(entity: "EntitySpec", raw: Mapping[str, Any]) -> dict[str, Any]:
    row: dict[str, Any] = {}
    for name, spec in entity.fields.items():
        value = get_path(raw, spec.path)
        if value in _EMPTY and spec.fallback_join:
            value = " ".join(str(raw[k]) for k in spec.fallback_join if raw.get(k) not in _EMPTY) or None
        row[name] = spec.default if value is None else value
    return row


class _BlankIfMissing(dict):
    def __missing__(self, key: str) -> str:
        return ""


def placeholders(template: str | None) -> list[str]:
    return [name for _, name, _, _ in string.Formatter().parse(template or "") if name]


def render(template: str, values: Mapping[str, Any]) -> str:
    return template.format_map(_BlankIfMissing(values))
