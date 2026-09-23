from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from . import constants as C
from .errors import ErpError
from .mapping import placeholders

# ---------------------------------------------------------------------------- specs

@dataclass(frozen=True)
class FieldSpec:
    name: str
    path: str
    type: str = C.FIELD_STRING
    default: Any = None
    fallback_join: tuple[str, ...] = ()


@dataclass(frozen=True)
class EntitySpec:
    name: str
    label: str
    path: str
    records_path: str
    fields: dict[str, FieldSpec]

    @property
    def source_fields(self) -> str:
        roots: list[str] = []
        for spec in self.fields.values():
            for candidate in (spec.path.split(".")[0], *spec.fallback_join):
                if candidate != "id" and candidate not in roots:
                    roots.append(candidate)
        return ",".join(roots)

    def field_type(self, name: str) -> str:
        spec = self.fields.get(name)
        return spec.type if spec else C.FIELD_STRING


@dataclass(frozen=True)
class PagingSpec:
    page_param: str
    size_param: str
    page_size: int
    max_pages: int
    more_path: str
    fields_param: str | None = None
    token_param: str | None = None
    next_token_path: str | None = None
    empty_status: int | None = None


@dataclass(frozen=True)
class OAuthSpec:
    client_id_env: str
    client_secret_env: str
    auth_server_default: str
    auth_servers: tuple[str, ...]
    authorize_path: str
    token_path: str
    token_header: str
    api_base_field: str
    api_base_default: str
    scopes: tuple[str, ...]
    label: str = "Sign in"
    scope_separator: str = " "
    auth_server_env: str | None = None
    auth_server_param: str | None = None
    revoke_path: str | None = None
    revoke_param: str = "token"
    authorize_params: dict[str, str] = field(default_factory=dict)
    account_info: dict[str, Any] | None = None

    @property
    def scope(self) -> str:
        return self.scope_separator.join(self.scopes)


@dataclass(frozen=True)
class InputSpec:
    name: str
    label: str
    kind: str = C.INPUT_TEXT
    required: bool = True
    default: str | None = None
    help: str | None = None


@dataclass(frozen=True)
class LoginSpec:
    path: str
    body: dict[str, Any]
    session_from: str
    session_key: str
    ttl_seconds: int = C.DEFAULT_SESSION_TTL_SECONDS


@dataclass(frozen=True)
class CredentialSpec:
    method: str
    label: str
    inputs: tuple[InputSpec, ...]
    api_base: str
    test_path: str
    headers: dict[str, str] = field(default_factory=dict)
    query: dict[str, str] = field(default_factory=dict)
    cookies: dict[str, str] = field(default_factory=dict)
    username: str | None = None
    password: str | None = None
    login: LoginSpec | None = None
    account_label: str | None = None

    @property
    def input_names(self) -> set[str]:
        return {i.name for i in self.inputs}


@dataclass(frozen=True)
class AuthSpec:
    methods: tuple[str, ...]
    oauth2: OAuthSpec | None
    credentials: dict[str, CredentialSpec]


@dataclass(frozen=True)
class MetricSpec:
    name: str
    label: str
    format: str
    entity: str | None = None
    agg: str | None = None
    field: str | None = None
    where: tuple[dict, ...] = ()
    ratio: tuple[str, str] | None = None
    percent: bool = False


@dataclass(frozen=True)
class ChartSpec:
    name: str
    title: str
    entity: str
    type: str
    value_format: str
    group_by: str | None = None
    value_field: str | None = None
    agg: str = C.AGG_SUM
    rank_by: str | None = None
    label_field: str | None = None
    top_n: int | None = None
    order: tuple[str, ...] = ()
    where: tuple[dict, ...] = ()
    color: str | None = None
    colors: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class TileSpec:
    metric: str
    label: str
    sub: str | None = None
    variant: str = C.VARIANT_DEFAULT


@dataclass(frozen=True)
class TabSpec:
    id: str
    label: str
    tiles: tuple[TileSpec, ...]
    charts: tuple[str, ...]


@dataclass(frozen=True)
class AssistantSpec:
    role: str
    presenter_role: str
    data_name: str
    scope_note: str
    out_of_scope_example: str
    intents: tuple[str, ...]
    planner_example: str
    categorical_fields_hint: str
    default_groupings: str
    presenter_examples: str
    fallback_endpoints: tuple[str, ...]
    fallback_charts: tuple[str, ...]
    fallback_headline: str
    fallback_summary: str
    out_of_scope_headline: str
    out_of_scope_summary: str
    summary_metrics: tuple[str, ...]
    summary_breakdowns: tuple[dict, ...]


@dataclass(frozen=True)
class Pack:
    id: str
    provider: str
    label: str
    currency_code: str
    currency_symbol: str
    currency_decimals: int
    auth: AuthSpec
    paging: PagingSpec
    entities: dict[str, EntitySpec]
    metrics: dict[str, MetricSpec]
    charts: dict[str, ChartSpec]
    tabs: tuple[TabSpec, ...]
    assistant: AssistantSpec

    def entity(self, name: str) -> EntitySpec:
        try:
            return self.entities[name]
        except KeyError:
            raise ErpError(ErpError.NOT_FOUND, f"Unknown data set '{name}'") from None

    def tab(self, tab_id: str) -> TabSpec:
        for tab in self.tabs:
            if tab.id == tab_id:
                return tab
        raise ErpError(ErpError.NOT_FOUND, f"Unknown dashboard tab '{tab_id}'")


# ---------------------------------------------------------------------------- loading

@lru_cache(maxsize=16)
def load_pack(path: str | Path) -> Pack:
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    pack = _parse_pack(raw)
    problems = _validate(pack)
    if problems:
        raise ErpError(ErpError.CONFIG, f"Invalid pack {path}:\n  - " + "\n  - ".join(problems))
    return pack


def _parse_pack(raw: Mapping[str, Any]) -> Pack:
    sets = {k: tuple(v) for k, v in (raw.get("sets") or {}).items()}
    currency = raw.get("currency") or {}
    dashboard = raw.get("dashboard") or {}
    return Pack(
        id=raw["id"],
        provider=raw.get("provider", raw["id"]),
        label=raw["label"],
        currency_code=currency.get("code", "USD"),
        currency_symbol=currency.get("symbol", "$"),
        currency_decimals=int(currency.get("decimals", 0)),
        auth=_parse_auth(raw.get("auth") or {}),
        paging=PagingSpec(**raw["paging"]),
        entities={name: _parse_entity(name, spec) for name, spec in raw["entities"].items()},
        metrics={name: _parse_metric(name, spec, sets) for name, spec in (raw.get("metrics") or {}).items()},
        charts={name: _parse_chart(name, spec, sets) for name, spec in (raw.get("charts") or {}).items()},
        tabs=tuple(_parse_tab(tab, raw.get("metrics") or {}) for tab in dashboard.get("tabs") or ()),
        assistant=_parse_assistant(raw["assistant"]),
    )


def _parse_auth(raw: Mapping[str, Any]) -> AuthSpec:
    unknown = [key for key in raw if key not in C.AUTH_METHODS]
    if unknown or not raw:
        raise ErpError(ErpError.CONFIG,
                       f"auth: needs one or more of {', '.join(C.AUTH_METHODS)} (got {', '.join(raw) or 'nothing'})")
    return AuthSpec(
        methods=tuple(raw),
        oauth2=_parse_oauth(raw[C.AUTH_OAUTH2]) if C.AUTH_OAUTH2 in raw else None,
        credentials={m: _parse_credentials(m, spec) for m, spec in raw.items() if m in C.CREDENTIAL_METHODS},
    )


def _parse_oauth(raw: Mapping[str, Any]) -> OAuthSpec:
    values = dict(raw)
    values["scopes"] = tuple(values.get("scopes") or ())
    values["auth_servers"] = tuple(s.rstrip("/") for s in values.get("auth_servers") or ())
    values["auth_server_default"] = values["auth_server_default"].rstrip("/")
    return OAuthSpec(**values)


def _parse_credentials(method: str, raw: Mapping[str, Any]) -> CredentialSpec:
    values = dict(raw)
    values["inputs"] = tuple(InputSpec(**item) for item in values.get("inputs") or ())
    for key in ("headers", "query", "cookies"):
        values[key] = dict(values.get(key) or {})
    if values.get("login"):
        login = dict(values["login"])
        login["body"] = dict(login.get("body") or {})
        values["login"] = LoginSpec(**login)
    values.setdefault("label", method.title())
    return CredentialSpec(method=method, **values)


def _parse_entity(name: str, raw: Mapping[str, Any]) -> EntitySpec:
    fields = {}
    for fname, spec in raw["fields"].items():
        spec = {"path": spec} if isinstance(spec, str) else dict(spec)
        spec["fallback_join"] = tuple(spec.get("fallback_join") or ())
        fields[fname] = FieldSpec(name=fname, **spec)
    return EntitySpec(
        name=name,
        label=raw.get("label", name.title()),
        path=raw["path"],
        records_path=raw["records_path"],
        fields=fields,
    )


def _resolve(value: Any, sets: Mapping[str, tuple], context: str) -> Any:
    if isinstance(value, str) and value.startswith(C.SET_REFERENCE_PREFIX):
        name = value[len(C.SET_REFERENCE_PREFIX):]
        if name not in sets:
            raise ErpError(ErpError.CONFIG, f"{context}: unknown set '{value}'")
        return list(sets[name])
    return value


def _parse_where(raw: Mapping[str, Any] | None, sets: Mapping[str, tuple], context: str) -> tuple[dict, ...]:
    filters = []
    for field_name, condition in (raw or {}).items():
        if not isinstance(condition, Mapping):
            condition = {C.OP_EQ: condition}
        for op, value in condition.items():
            filters.append({"field": field_name, "op": op, "value": _resolve(value, sets, context)})
    return tuple(filters)


def _parse_metric(name: str, raw: Mapping[str, Any], sets: Mapping[str, tuple]) -> MetricSpec:
    return MetricSpec(
        name=name,
        label=raw.get("label", name.replace("_", " ").title()),
        format=raw.get("format", C.FMT_NUMBER),
        entity=raw.get("entity"),
        agg=raw.get("agg"),
        field=raw.get("field"),
        where=_parse_where(raw.get("where"), sets, f"metric {name}"),
        ratio=tuple(raw["ratio"]) if raw.get("ratio") else None,
        percent=bool(raw.get("percent", False)),
    )


def _parse_chart(name: str, raw: Mapping[str, Any], sets: Mapping[str, tuple]) -> ChartSpec:
    values = dict(raw)
    values["order"] = tuple(_resolve(values.get("order") or (), sets, f"chart {name}"))
    values["where"] = _parse_where(values.get("where"), sets, f"chart {name}")
    values["colors"] = dict(values.get("colors") or {})
    values.setdefault("value_format", C.FMT_NUMBER)
    return ChartSpec(name=name, **values)


def _parse_tab(raw: Mapping[str, Any], metrics_raw: Mapping[str, Any]) -> TabSpec:
    tiles = []
    for tile in raw.get("tiles") or ():
        metric = tile["metric"]
        default_label = (metrics_raw.get(metric) or {}).get("label", metric)
        tiles.append(TileSpec(
            metric=metric,
            label=tile.get("label", default_label),
            sub=tile.get("sub"),
            variant=tile.get("variant", C.VARIANT_DEFAULT),
        ))
    return TabSpec(id=raw["id"], label=raw["label"], tiles=tuple(tiles), charts=tuple(raw.get("charts") or ()))


def _parse_assistant(raw: Mapping[str, Any]) -> AssistantSpec:
    values = dict(raw)
    for key in ("intents", "fallback_endpoints", "fallback_charts", "summary_metrics", "summary_breakdowns"):
        values[key] = tuple(values.get(key) or ())
    return AssistantSpec(**values)


# ---------------------------------------------------------------------------- validation

def _validate(pack: Pack) -> list[str]:
    problems: list[str] = []

    def need(ok: bool, message: str) -> None:
        if not ok:
            problems.append(message)

    def check_fields(entity_name: str | None, names: list[str | None], context: str) -> None:
        entity = pack.entities.get(entity_name or "")
        need(entity is not None, f"{context}: unknown entity '{entity_name}'")
        for name in names:
            if entity is not None and name is not None:
                need(name in entity.fields, f"{context}: unknown field '{name}' on '{entity_name}'")

    def check_where(entity_name: str | None, where: tuple[dict, ...], context: str) -> None:
        check_fields(entity_name, [f["field"] for f in where], context)
        for f in where:
            need(f["op"] in C.OPERATORS, f"{context}: unknown operator '{f['op']}'")

    for spec in pack.auth.credentials.values():
        problems.extend(_credential_problems(spec))

    for entity in pack.entities.values():
        for spec in entity.fields.values():
            need(spec.type in C.FIELD_TYPES, f"entity {entity.name}.{spec.name}: unknown type '{spec.type}'")

    for metric in pack.metrics.values():
        ctx = f"metric {metric.name}"
        need(metric.format in C.FORMATS, f"{ctx}: unknown format '{metric.format}'")
        if metric.ratio:
            for ref in metric.ratio:
                need(ref in pack.metrics, f"{ctx}: ratio refers to unknown metric '{ref}'")
        else:
            need(metric.agg in C.AGGREGATIONS, f"{ctx}: unknown agg '{metric.agg}'")
            need(metric.agg == C.AGG_COUNT or metric.field is not None, f"{ctx}: '{metric.agg}' needs a field")
            check_fields(metric.entity, [metric.field], ctx)
            check_where(metric.entity, metric.where, ctx)

    for chart in pack.charts.values():
        ctx = f"chart {chart.name}"
        need(chart.type in C.CHART_TYPES, f"{ctx}: unknown type '{chart.type}'")
        need(chart.value_format in C.FORMATS, f"{ctx}: unknown value_format '{chart.value_format}'")
        need(bool(chart.group_by) != bool(chart.rank_by), f"{ctx}: set exactly one of group_by / rank_by")
        need(chart.agg in C.AGGREGATIONS, f"{ctx}: unknown agg '{chart.agg}'")
        check_fields(chart.entity, [chart.group_by, chart.value_field, chart.rank_by, chart.label_field], ctx)
        check_where(chart.entity, chart.where, ctx)

    for tab in pack.tabs:
        for tile in tab.tiles:
            need(tile.metric in pack.metrics, f"tab {tab.id}: unknown metric '{tile.metric}'")
            need(tile.variant in C.VARIANTS, f"tab {tab.id}: unknown variant '{tile.variant}'")
            for ref in placeholders(tile.sub):
                need(ref in pack.metrics, f"tab {tab.id}: sub refers to unknown metric '{ref}'")
        for chart in tab.charts:
            need(chart in pack.charts, f"tab {tab.id}: unknown chart '{chart}'")

    a = pack.assistant
    for name in a.fallback_endpoints:
        need(name in pack.entities, f"assistant.fallback_endpoints: unknown entity '{name}'")
    for name in a.fallback_charts:
        need(name in pack.charts, f"assistant.fallback_charts: unknown chart '{name}'")
    for name in a.summary_metrics:
        need(name in pack.metrics, f"assistant.summary_metrics: unknown metric '{name}'")
    for item in a.summary_breakdowns:
        check_fields(item.get("entity"), [item.get("group_by")], "assistant.summary_breakdowns")
    return problems


def _credential_problems(spec: CredentialSpec) -> list[str]:
    ctx = f"auth.{spec.method}"
    problems: list[str] = []

    def need(ok: bool, message: str) -> None:
        if not ok:
            problems.append(f"{ctx}: {message}")

    names = [i.name for i in spec.inputs]
    need(bool(names), "needs at least one input")
    need(len(names) == len(set(names)), "input names must be unique")
    need(C.SESSION_PLACEHOLDER not in names, f"'{C.SESSION_PLACEHOLDER}' is reserved, rename that input")
    for item in spec.inputs:
        need(item.kind in C.INPUT_KINDS, f"input '{item.name}': unknown kind '{item.kind}'")

    def check_templates(templates: Mapping[str, Any], where: str, *, session_ok: bool) -> None:
        allowed = spec.input_names | ({C.SESSION_PLACEHOLDER} if session_ok else set())
        for key, template in templates.items():
            label = f"{where}.{key}" if where else key
            for ref in placeholders(template if isinstance(template, str) else None):
                need(ref in allowed, f"{label} uses unknown input '{{{ref}}}'")

    check_templates({"api_base": spec.api_base, "account_label": spec.account_label or ""}, "", session_ok=False)
    has_session = spec.login is not None
    for where in ("headers", "query", "cookies"):
        check_templates(getattr(spec, where), where, session_ok=has_session)

    if spec.method == C.AUTH_TOKEN:
        need(bool(spec.headers or spec.query or spec.cookies), "set headers, query or cookies to send the token")
    if spec.method == C.AUTH_BASIC:
        for role in ("username", "password"):
            need(getattr(spec, role) in spec.input_names, f"'{role}' must name one of the inputs")
    if spec.method == C.AUTH_SESSION:
        need(has_session, "needs a login: block")
    if has_session:
        need(spec.login.session_from in C.SESSION_SOURCES, f"login.session_from must be one of {sorted(C.SESSION_SOURCES)}")
        check_templates(spec.login.body, "login.body", session_ok=False)
        uses_session = any(C.SESSION_PLACEHOLDER in placeholders(t)
                           for t in (*spec.headers.values(), *spec.query.values(), *spec.cookies.values()))
        need(uses_session, "headers, query or cookies must use {session}")
    return problems
