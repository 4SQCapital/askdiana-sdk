from __future__ import annotations

import string
from collections.abc import Mapping
from datetime import date, timedelta
from typing import TYPE_CHECKING, Any

from . import constants as C

if TYPE_CHECKING:
    from .pack import EntitySpec

_EMPTY = (None, "")


def get_path(obj: Any, path: str | None) -> Any:
    if not path:
        return None
    if isinstance(obj, Mapping) and path in obj:  # a key with dots in it, e.g. "@odata.nextLink"
        return obj[path]
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
    derived = []
    for name, spec in entity.fields.items():
        if spec.derive:
            derived.append(spec)
            continue
        value = get_path(raw, spec.path)
        if value in _EMPTY and spec.fallback_join:
            value = " ".join(str(raw[k]) for k in spec.fallback_join if raw.get(k) not in _EMPTY) or None
        if spec.type == C.FIELD_MONTH and isinstance(value, str):
            value = value[:7]
        elif spec.type in _NUMERIC_TYPES and isinstance(value, str):
            value = _number(value)
        row[name] = spec.default if value is None else value
    for spec in derived:
        row[spec.name] = _derive(spec.derive, row, spec.default)
    return row


_NUMERIC_TYPES = frozenset({C.FIELD_NUMBER, C.FIELD_MONEY, C.FIELD_PERCENT})


def _number(text: str) -> float | str:
    """Some APIs send decimals as strings ("120.0", Sage); a blank or non-numeric string stays as it is."""
    try:
        return float(text)
    except ValueError:
        return text


def _derive(rules, row: Mapping[str, Any], default: Any) -> Any:
    from .query import apply_filters
    today = date.today()
    for value, where in rules:
        filters = [{**f, "value": date_token(f["value"], today)} for f in where]
        if not filters or apply_filters([dict(row)], filters):
            return value
    return default


def date_token(value: Any, today: date) -> Any:
    """'@today', '@today+7', '@today-30', '@month_start', '@year_start' as YYYY-MM-DD; anything else unchanged."""
    match = C.DATE_TOKEN_RE.match(value) if isinstance(value, str) else None
    if not match:
        return value
    if match["today"]:
        return (today + timedelta(days=int(match["days"] or 0))).isoformat()
    return today.replace(day=1).isoformat() if match["start"] == "month" else today.replace(month=1, day=1).isoformat()


class _BlankIfMissing(dict):
    def __missing__(self, key: str) -> str:
        return ""


def placeholders(template: str | None) -> list[str]:
    return [name for _, name, _, _ in string.Formatter().parse(template or "") if name]


def render(template: str, values: Mapping[str, Any]) -> str:
    return template.format_map(_BlankIfMissing(values))
