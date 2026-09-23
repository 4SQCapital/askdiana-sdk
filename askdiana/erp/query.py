from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from . import constants as C

_OPS: dict[str, Callable[[Any, Any], bool]] = {
    C.OP_EQ: lambda a, b: a == b,
    C.OP_NEQ: lambda a, b: a != b,
    C.OP_GT: lambda a, b: a > b,
    C.OP_GTE: lambda a, b: a >= b,
    C.OP_LT: lambda a, b: a < b,
    C.OP_LTE: lambda a, b: a <= b,
    C.OP_CONTAINS: lambda a, b: str(b).lower() in str(a).lower(),
    C.OP_IN: lambda a, b: a in b,
    C.OP_NOT_IN: lambda a, b: a not in b,
}


def is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def apply_filters(rows: Iterable[Any], filters: Sequence[Mapping[str, Any]] | None) -> list[dict]:
    dict_rows = [r for r in rows if isinstance(r, dict)]
    if not filters:
        return dict_rows
    kept = []
    for row in dict_rows:
        for f in filters:
            fn = _OPS.get(f.get("op", C.OP_EQ))
            actual = row.get(f.get("field"))
            try:
                if fn is None or actual is None or not fn(actual, f.get("value")):
                    break
            except TypeError:
                break
        else:
            kept.append(row)
    return kept


def aggregate(rows: Sequence[dict], *, agg: str, field: str | None = None) -> float:
    if agg == C.AGG_COUNT:
        return float(len(rows))
    if agg == C.AGG_COUNT_DISTINCT:
        return float(len({row.get(field) for row in rows if row.get(field) is not None}))
    values = [row[field] for row in rows if is_number(row.get(field))]
    if agg == C.AGG_AVG:
        return sum(values) / len(values) if values else 0.0
    return float(sum(values))


def group_values(rows: Sequence[dict], *, group_by: str, value_field: str | None = None,
                agg: str = C.AGG_SUM) -> dict[str, float] | None:
    sums: dict[str, float] = {}
    counts: dict[str, int] = {}
    numeric_seen = False
    for row in rows:
        key = row.get(group_by)
        if key is None:
            continue
        label = str(key)
        counts[label] = counts.get(label, 0) + 1
        value = row.get(value_field) if value_field else 1
        if value_field and is_number(value):
            numeric_seen = True
        sums[label] = sums.get(label, 0.0) + (value if is_number(value) else 0.0)
    if not counts or (value_field and not numeric_seen and agg != C.AGG_COUNT):
        return None
    if agg == C.AGG_COUNT:
        return {k: float(v) for k, v in counts.items()}
    if agg == C.AGG_AVG:
        return {k: sums[k] / counts[k] for k in sums}
    return sums


def order_groups(grouped: Mapping[str, float], *, order: Sequence[str] = (),
                top_n: int | None = None) -> list[tuple[str, float]]:
    by_value = sorted(grouped.items(), key=lambda kv: -kv[1])
    if order:
        known = set(order)
        fixed = [(k, grouped[k]) for k in order if k in grouped]
        rest = [kv for kv in by_value if kv[0] not in known]
        ordered = fixed + rest
    else:
        ordered = by_value
    return ordered[:top_n] if top_n else ordered


def rank_rows(rows: Sequence[dict], *, label_field: str, value_field: str,
            top_n: int | None) -> list[tuple[str, float]]:
    ranked = sorted((r for r in rows if is_number(r.get(value_field))), key=lambda r: -r[value_field])
    ranked = ranked[:top_n] if top_n else ranked
    return [(str(r.get(label_field)), float(r[value_field])) for r in ranked]


# ---------------------------------------------------------------- formatting

def format_value(value: float | None, fmt: str, *, symbol: str, decimals: int) -> str:
    if value is None:
        return "—"
    if fmt == C.FMT_CURRENCY:
        return f"{symbol}{value:,.{decimals}f}"
    if fmt == C.FMT_CURRENCY_COMPACT:
        if abs(value) >= C.COMPACT_MILLION:
            return f"{symbol}{value / C.COMPACT_MILLION:.1f}M"
        if abs(value) >= C.COMPACT_THOUSAND:
            return f"{symbol}{value / C.COMPACT_THOUSAND:.0f}K"
        return f"{symbol}{value:.0f}"
    if fmt == C.FMT_PERCENT:
        return f"{value:.0f}%"
    if fmt == C.FMT_DECIMAL1:
        return f"{value:.1f}"
    return f"{round(value):,}"


def format_cell(value: Any, field_type: str, *, symbol: str, decimals: int) -> Any:
    if not is_number(value) or field_type == C.FIELD_ID:
        return value
    if field_type == C.FIELD_PERCENT:
        return format_value(value, C.FMT_PERCENT, symbol=symbol, decimals=decimals)
    if field_type == C.FIELD_MONEY:
        return format_value(value, C.FMT_CURRENCY, symbol=symbol, decimals=decimals)
    return f"{value:,.2f}" if isinstance(value, float) else f"{value:,}"


# ---------------------------------------------------------------- tables

@dataclass(frozen=True)
class Table:
    entity: str
    title: str
    headers: list[str]
    display_rows: list[list[Any]]
    all_rows: list[list[Any]]
    total_count: int


def build_table(rows: Sequence[dict], *, entity: str, title: str, columns: Sequence[str],
                field_type: Callable[[str], str], symbol: str, decimals: int,
                sort_by: str | None = None, sort_desc: bool = False,
                filters: Sequence[Mapping[str, Any]] | None = None) -> Table | None:
    dict_rows = apply_filters(rows, filters)
    real_columns = [c for c in columns if any(c in r for r in dict_rows)]
    if not dict_rows or not real_columns:
        return None
    if sort_by and any(sort_by in r for r in dict_rows):
        dict_rows = sorted(dict_rows, key=lambda r: (r.get(sort_by) is None, r.get(sort_by)), reverse=sort_desc)
    all_rows = [[r.get(c, "") for c in real_columns] for r in dict_rows]
    display = [[format_cell(v, field_type(c), symbol=symbol, decimals=decimals) for c, v in zip(real_columns, row)]
            for row in all_rows[:C.TABLE_DISPLAY_CAP]]
    return Table(entity, title, real_columns, display, all_rows, len(all_rows))
