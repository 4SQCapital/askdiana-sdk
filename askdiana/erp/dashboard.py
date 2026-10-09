from __future__ import annotations

import string
from collections.abc import Mapping

from .charts import pack_series, to_points
from .metrics import entities_for, evaluate_all, format_metric
from .pack import Pack, TabSpec


def tab_index(pack: Pack) -> list[dict]:
    return [{"id": tab.id, "label": tab.label} for tab in pack.tabs]


def entity_index(pack: Pack) -> list[dict]:
    return [{
        "name": entity.name,
        "label": entity.label,
        "fields": [{"name": spec.name, "type": spec.type} for spec in entity.fields.values()],
    } for entity in pack.entities.values()]


def _sub_metrics(tab: TabSpec) -> list[str]:
    return [name for tile in tab.tiles for _, name, _, _ in string.Formatter().parse(tile.sub or "") if name]


def _bar_metrics(tab: TabSpec) -> list[str]:
    return [segment.metric for bar in tab.bars for segment in bar.segments]


def _headline_metrics(tab: TabSpec) -> list[str]:
    return [name for line in tab.headlines for _, name, _, _ in string.Formatter().parse(line) if name]


def _chart_metrics(pack: Pack, tab: TabSpec) -> list[str]:
    return [metric for name in tab.charts for metric in pack.charts[name].metrics]


def _tab_metrics(pack: Pack, tab: TabSpec) -> list[str]:
    return ([t.metric for t in tab.tiles] + _sub_metrics(tab) + _bar_metrics(tab) + _headline_metrics(tab)
            + _chart_metrics(pack, tab))


def entities_for_tab(pack: Pack, tab: TabSpec) -> list[str]:
    needed = entities_for(pack, _tab_metrics(pack, tab))
    needed |= {pack.charts[name].entity for name in tab.charts if pack.charts[name].entity}
    return sorted(needed)


def build_tab(pack: Pack, tab: TabSpec, data: Mapping[str, list[dict]]) -> dict:
    values = evaluate_all(pack, _tab_metrics(pack, tab), data)
    formatted = {name: format_metric(pack, name, value) for name, value in values.items()}
    tiles = [{
        "label": tile.label,
        "value": formatted[tile.metric],
        "sub": tile.sub.format(**formatted) if tile.sub else None,
        "variant": tile.variant,
        "group": tile.group,
    } for tile in tab.tiles]
    charts = []
    for name in tab.charts:
        spec = pack.charts[name]
        if spec.metrics:
            series = [(pack.metrics[m].label, float(values.get(m) or 0)) for m in spec.metrics]
        else:
            series = pack_series(spec, data.get(spec.entity, []))
        charts.append({
            "id": name, "title": spec.title, "type": spec.type, "value_format": spec.value_format,
            "data": to_points(spec, series),
        })
    bars = []
    for bar in tab.bars:
        amounts = [float(values.get(s.metric) or 0) for s in bar.segments]
        bars.append({
            "title": bar.title,
            "total": format_metric(pack, bar.segments[0].metric, sum(amounts)),
            "segments": [{"label": s.label, "value": formatted[s.metric], "amount": amount, "color": s.color}
                         for s, amount in zip(bar.segments, amounts)],
        })
    headlines = [line.format(**formatted) for line in tab.headlines]
    return {"id": tab.id, "label": tab.label, "tiles": tiles, "charts": charts, "bars": bars, "headlines": headlines}
