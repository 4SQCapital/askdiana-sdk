from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from . import constants as C
from .pack import ChartSpec
from .query import apply_filters, group_values, order_groups, rank_rows

Series = list[tuple[str, float]]


def pack_series(spec: ChartSpec, rows: list[dict]) -> Series:
    rows = apply_filters(rows, spec.where)
    if spec.rank_by:
        return rank_rows(rows, label_field=spec.label_field or spec.rank_by, value_field=spec.rank_by, top_n=spec.top_n)
    grouped = group_values(rows, group_by=spec.group_by, value_field=spec.value_field, agg=spec.agg)
    return order_groups(grouped or {}, order=spec.order, top_n=spec.top_n)


def presenter_series(spec: Mapping[str, Any], data: Mapping[str, list[dict]]) -> Series | None:
    rows = data.get(spec.get("endpoint") or "")
    group_by = spec.get("group_by")
    if not rows or not group_by:
        return None
    grouped = group_values(apply_filters(rows, spec.get("filters")), group_by=group_by,
                        value_field=spec.get("value_field"), agg=spec.get("agg", C.AGG_SUM))
    if not grouped:
        return None
    series = order_groups(grouped, top_n=max(1, int(spec.get("top_n") or C.DEFAULT_TOP_N)))
    return series if len(series) >= C.MIN_CHAT_CHART_GROUPS else None


def to_points(spec: ChartSpec, series: Series) -> list[dict]:
    return [{"label": label, "value": value, "color": spec.colors.get(label, spec.color)} for label, value in series]
