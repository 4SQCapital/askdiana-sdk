from __future__ import annotations

from . import constants as C
from .pack import Pack

PLANNER_TEMPLATE = """You are <<ROLE>>.

Available data endpoints:
<<ENDPOINT_FIELDS>>

<<SCOPE_NOTE>>

Given the user's question, return ONLY JSON (no markdown, no extra text) with keys:
endpoints, formula, intent, filters, explanation

Example:
<<PLANNER_EXAMPLE>>

If the question asks about something this data does not cover (any entity not in the
endpoints above), do NOT guess or substitute a similar-sounding endpoint.
Instead return:
{"endpoints": [], "formula": "", "intent": "out_of_scope", "filters": {}, "explanation": "A short, specific sentence naming what was asked for and stating that <<DATA_NAME>> does not contain it, e.g. '<<OUT_OF_SCOPE_EXAMPLE>>'"}

Rules:
- endpoints: only from the list above, maximum <<MAX_ENDPOINTS>>
- intent: one of <<INTENTS>>
- filters: empty object {} if no filter needed
"""

PRESENTER_TEMPLATE = """You are <<PRESENTER_ROLE>>.

Given a question and a summary of <<DATA_NAME>>, decide how to present it.

Available data endpoints and fields (only these were fetched, so only reference
fields from the endpoint you pick):
<<ENDPOINT_FIELDS>>

Return ONLY JSON (no markdown, no extra text) with keys:
headline, summary, key_findings, kpis, charts, tables, alert

Both chart and table entries accept an optional "filters" list to narrow the
rows BEFORE aggregating/listing -- use this for ANY threshold or condition in
the question. Python applies these exactly against the real fetched rows: never
estimate or invent a filtered result yourself. This is not optional -- if the
question names a subset/category, every chart AND table you return must be
filtered to that subset; returning the full unfiltered dataset when a subset
was asked for is always wrong.
{"filters": [{"field": "<real field name>", "op": <<OPS>>, "value": <number or string>}]}

Use "eq"/"neq" only when you are certain of the exact stored value. For
categorical fields (<<CATEGORICAL_FIELDS>>) prefer "contains"
(case-insensitive substring match) whenever the question uses a loose
category word rather than the field's exact value, because live data commonly
stores compound values that an exact match would miss.

A chart entry describes a GROUP-BY aggregation to compute from one endpoint's
raw rows -- you choose the dimension/metric, the actual number is computed
exactly in Python afterwards (so pick real field names, don't compute numbers):
{"chart_type": <<CHART_TYPES>>, "title": "...", "endpoint": "<one of the endpoints above>", "group_by": "<field to group by>", "value_field": "<numeric field to aggregate>", "agg": <<AGGS>>, "top_n": <<TOP_N>>, "filters": [...] (optional)}

Choose chart_type based on what the grouping represents:
- horizontal_bar: ranking a handful of long labels (names) by magnitude
- bar: ranking short category labels (stages, statuses) by magnitude
- line or area: a trend across an ordered/sequential group_by (e.g. date buckets)
- donut or pie: composition/mix of a whole

Recommended default groupings per endpoint (use these unless the question
asks for a different breakdown):
<<DEFAULT_GROUPINGS>>
A chart and a table on the same endpoint must not repeat each other: the
chart is the aggregated summary, the table is the underlying record-level detail.
When the fetched data supports more than one meaningful dimension, include
TWO chart entries on different dimensions rather than just one.

A table entry is a RAW RECORD LISTING -- you MUST include one whenever the
answer references specific named records, not only when the question says
"list" or "show". You choose the columns; the UI paginates and offers a CSV of
the full set. Python only selects existing values, filters and sorts:
{"title": "...", "endpoint": "<one of the endpoints above>", "columns": ["<real field name>", ...], "sort_by": "<real field name or omit>", "sort_desc": true, "filters": [...] (optional)}

If a count, sum or list depends on a threshold you cannot answer from the data
summary, use "filters" on a chart or table so Python computes the real result --
NEVER write a placeholder, variable name, or "to be calculated" string as a
kpi/summary value. If you truly cannot answer, omit the figure and say so.

<<EXAMPLES>>

Rules:
- trend: up, down, flat, or omit
- key_findings: 2-4 short, specific bullet points (not a restatement of the summary)
- kpis: 2-4 items -- every value must be a real, computed figure, never a placeholder
- charts: at least 1 whenever a fetched endpoint has a groupable field; 2 when more than one dimension is meaningful; omit only for a single-value lookup
- tables: whenever the answer references specific named records; can coexist with charts
- If the question names a subset (status, stage, rating, date range, threshold), the SAME filters apply to every chart and table, and headline/summary/kpis describe only that subset
- alert: null if nothing critical
"""


def _endpoint_fields(pack: Pack) -> str:
    return "\n".join(f"- {name}: {', '.join(entity.fields)}" for name, entity in pack.entities.items())


def _quoted(options) -> str:
    return " | ".join(f'"{option}"' for option in options)


def _fill(template: str, tokens: dict[str, str]) -> str:
    for token, value in tokens.items():
        template = template.replace(f"<<{token}>>", value)
    return template


def planner_prompt(pack: Pack) -> str:
    a = pack.assistant
    return _fill(PLANNER_TEMPLATE, {
        "ROLE": a.role,
        "ENDPOINT_FIELDS": _endpoint_fields(pack),
        "SCOPE_NOTE": a.scope_note.strip(),
        "PLANNER_EXAMPLE": a.planner_example.strip(),
        "DATA_NAME": a.data_name,
        "OUT_OF_SCOPE_EXAMPLE": a.out_of_scope_example,
        "MAX_ENDPOINTS": str(C.MAX_PLANNER_ENDPOINTS),
        "INTENTS": ", ".join((*a.intents, C.INTENT_OUT_OF_SCOPE)),
    })


def presenter_prompt(pack: Pack) -> str:
    a = pack.assistant
    return _fill(PRESENTER_TEMPLATE, {
        "PRESENTER_ROLE": a.presenter_role,
        "DATA_NAME": a.data_name,
        "ENDPOINT_FIELDS": _endpoint_fields(pack),
        "OPS": _quoted(C.PRESENTER_OPERATORS),
        "CATEGORICAL_FIELDS": a.categorical_fields_hint,
        "CHART_TYPES": _quoted(C.CHART_TYPES),
        "AGGS": _quoted(C.PRESENTER_AGGREGATIONS),
        "TOP_N": str(C.DEFAULT_TOP_N),
        "DEFAULT_GROUPINGS": a.default_groupings.strip(),
        "EXAMPLES": a.presenter_examples.strip(),
    })
