from __future__ import annotations

from collections.abc import Iterable, Mapping

from .pack import Pack
from .query import aggregate, apply_filters, format_value


def evaluate(pack: Pack, name: str, data: Mapping[str, list[dict]]) -> float | None:
    spec = pack.metrics[name]
    if spec.ratio:
        numerator = evaluate(pack, spec.ratio[0], data)
        denominator = evaluate(pack, spec.ratio[1], data)
        if numerator is None or denominator is None:
            return None
        value = numerator / denominator if denominator else 0.0
        return value * 100 if spec.percent else value
    rows = data.get(spec.entity)
    if rows is None:
        return None
    return aggregate(apply_filters(rows, spec.where), agg=spec.agg, field=spec.field)


def evaluate_all(pack: Pack, names: Iterable[str], data: Mapping[str, list[dict]]) -> dict[str, float | None]:
    return {name: evaluate(pack, name, data) for name in dict.fromkeys(names)}


def format_metric(pack: Pack, name: str, value: float | None) -> str:
    return format_value(value, pack.metrics[name].format,
                        symbol=pack.currency_symbol, decimals=pack.currency_decimals)


def entities_for(pack: Pack, names: Iterable[str]) -> set[str]:
    needed: set[str] = set()
    for name in names:
        spec = pack.metrics[name]
        needed |= entities_for(pack, spec.ratio) if spec.ratio else {spec.entity}
    return needed
