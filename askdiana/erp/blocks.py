from __future__ import annotations

import base64
import csv
import io
from typing import Any
from urllib.parse import quote

from . import constants as C
from .charts import pack_series, presenter_series
from .pack import Pack
from .pipeline import Answer
from .query import Table, build_table, format_value, is_number


def build_blocks(pack: Pack, answer: Answer) -> list[dict]:
    presentation, data = answer.presentation, answer.data
    tables = _tables(pack, presentation, data)

    headline, summary, kpis = presentation.get("headline"), presentation.get("summary"), presentation.get("kpis") or []
    if tables:
        headline, summary, kpis = _grounded_text(pack, tables[0])

    blocks: list[dict] = []
    if _real(headline):
        blocks.append({"type": "text", "style": "heading", "content": headline})
    if _real(summary):
        blocks.append({"type": "text", "content": summary})
    kpi_rows = [[k.get("label", ""), f"{k.get('value', '')}{_delta(k.get('delta'))}"] for k in kpis if _real(k.get("value"))]
    if kpi_rows:
        blocks.append({"type": "table", "headers": ["Metric", "Value"], "rows": kpi_rows})
    findings = [f for f in presentation.get("key_findings") or [] if _real(f)]
    if findings:
        blocks += [{"type": "text", "style": "bold", "content": "Key Findings"}, {"type": "list", "items": findings}]

    blocks += _charts(pack, presentation, data)
    for table in tables:
        blocks += _table_blocks(table)

    for name in answer.truncated:
        cap = pack.paging.page_size * pack.paging.max_pages
        blocks.append({"type": "alert", "variant": "warning",
                    "content": f"Only the first {cap:,} {pack.entities[name].label} were read."})
    if _real(presentation.get("alert")):
        blocks.append({"type": "alert", "variant": "warning", "content": presentation["alert"]})
    return blocks


# ------------------------------------------------------------------ pieces

def _real(value: Any) -> bool:
    return bool(value) and not C.PLACEHOLDER_RE.search(str(value))


def _delta(delta: Any) -> str:
    text = str(delta or "").strip()
    return f" ({text})" if text and text.lower() != "none" else ""


def _table(pack: Pack, data: dict, spec: dict) -> Table | None:
    entity_name = spec.get("endpoint")
    rows = data.get(entity_name or "")
    if not rows:
        return None
    entity = pack.entities[entity_name]
    return build_table(rows, entity=entity_name, title=spec.get("title") or entity.label,
                    columns=spec.get("columns") or [], field_type=entity.field_type,
                    symbol=pack.currency_symbol, decimals=pack.currency_decimals,
                    sort_by=spec.get("sort_by"), sort_desc=bool(spec.get("sort_desc")),
                    filters=spec.get("filters"))


def _tables(pack: Pack, presentation: dict, data: dict) -> list[Table]:
    tables = [t for t in (_table(pack, data, spec) for spec in presentation.get("tables") or []) if t]
    if tables:
        return tables
    for name, rows in data.items():
        scalar = [k for k, v in (rows[0].items() if rows else []) if not isinstance(v, (dict, list))]
        table = _table(pack, data, {"endpoint": name, "columns": scalar[:C.FALLBACK_TABLE_MAX_COLUMNS],
                                    "title": pack.entities[name].label})
        if table:
            return [table]
    return []


def _money_total(pack: Pack, table: Table) -> tuple[str, float] | None:
    entity = pack.entities[table.entity]
    for index, column in enumerate(table.headers):
        if entity.field_type(column) == C.FIELD_MONEY:
            return column.replace("_", " "), sum(r[index] for r in table.all_rows if is_number(r[index]))
    return None


def _grounded_text(pack: Pack, table: Table) -> tuple[str, str, list[dict]]:
    title = table.title
    headline = f"{table.total_count} {title}"
    summary = f"There are {table.total_count} {title[:1].lower() + title[1:]}"
    kpis = [{"label": f"Number of {title}", "value": f"{table.total_count:,}"}]
    money = _money_total(pack, table)
    if money:
        column, total = money
        amount = format_value(total, C.FMT_CURRENCY, symbol=pack.currency_symbol, decimals=pack.currency_decimals)
        summary += f", totalling {amount} ({column})"
        kpis.append({"label": column if column.lower().startswith("total") else f"Total {column}", "value": amount})
    return headline, summary + ".", kpis


def _charts(pack: Pack, presentation: dict, data: dict) -> list[dict]:
    blocks = []
    for spec in presentation.get("charts") or []:
        series = presenter_series(spec, data)
        if series:
            blocks.append({"type": "chart", "chart_type": spec.get("chart_type", C.CHART_BAR),
                        "title": spec.get("title", ""), "data": [{"label": l, "value": v} for l, v in series]})
    if blocks:
        return blocks
    for name in pack.assistant.fallback_charts:
        chart = pack.charts[name]
        rows = data.get(chart.entity)
        series = pack_series(chart, rows) if rows else []
        if len(series) >= C.MIN_CHAT_CHART_GROUPS:
            return [{"type": "chart", "chart_type": C.CHART_BAR, "title": chart.title,
                    "data": [{"label": l, "value": v} for l, v in series]}]
    return []


def _csv_url(table: Table) -> str:
    buffer = io.StringIO()
    csv.writer(buffer).writerows([table.headers, *table.all_rows])
    encoded = base64.urlsafe_b64encode(buffer.getvalue().encode("utf-8")).decode("ascii")
    filename = f"{table.title.lower().replace(' ', '-')}.csv"
    return f"{C.EXPORT_CSV_PATH}?data={quote(encoded)}&filename={quote(filename)}"


def _table_blocks(table: Table) -> list[dict]:
    shown = len(table.display_rows)
    more = table.total_count > shown
    filename = f"{table.title.lower().replace(' ', '-')}.csv"
    return [
        {"type": "text", "style": "bold",
        "content": f"{table.title} (showing {shown} of {table.total_count})" if more else table.title},
        {"type": "table", "headers": table.headers, "rows": table.display_rows,
        "total_count": table.total_count, "page_size": C.TABLE_PAGE_SIZE},
        {"type": "buttons", "items": [{
            "label": f"Download CSV ({table.total_count} rows)" if more else "Download CSV",
            "url": _csv_url(table), "style": "outline", "download": filename,
        }]},
    ]
