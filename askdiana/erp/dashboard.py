from __future__ import annotations

import string
from collections.abc import Mapping

from .charts import pack_series, to_points
from .metrics import entities_for, evaluate_all, format_metric
from .pack import Pack, TabSpec


def tab_index(pack: Pack) -> list[dict]:
    return [{"id": tab.id, "label": tab.label} for tab in pack.tabs]


def _sub_metrics(tab: TabSpec) -> list[str]:
    return [name for tile in tab.tiles for _, name, _, _ in string.Formatter().parse(tile.sub or "") if name]


def entities_for_tab(pack: Pack, tab: TabSpec) -> list[str]:
    needed = entities_for(pack, [t.metric for t in tab.tiles] + _sub_metrics(tab))
    needed |= {pack.charts[name].entity for name in tab.charts}
    return sorted(needed)


def build_tab(pack: Pack, tab: TabSpec, data: Mapping[str, list[dict]]) -> dict:
    values = evaluate_all(pack, [t.metric for t in tab.tiles] + _sub_metrics(tab), data)
    formatted = {name: format_metric(pack, name, value) for name, value in values.items()}
    tiles = [{
        "label": tile.label,
        "value": formatted[tile.metric],
        "sub": tile.sub.format(**formatted) if tile.sub else None,
        "variant": tile.variant,
    } for tile in tab.tiles]
    charts = []
    for name in tab.charts:
        spec = pack.charts[name]
        charts.append({
            "id": name, "title": spec.title, "type": spec.type, "value_format": spec.value_format,
            "data": to_points(spec, pack_series(spec, data.get(spec.entity, []))),
        })
    return {"id": tab.id, "label": tab.label, "tiles": tiles, "charts": charts}
