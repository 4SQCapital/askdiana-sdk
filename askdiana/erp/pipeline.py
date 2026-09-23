from __future__ import annotations

import logging
from dataclasses import dataclass, field

import requests

from . import constants as C
from .errors import ErpError
from .llm import LLMClient
from .metrics import evaluate_all, format_metric
from .pack import Pack
from .prompts import planner_prompt, presenter_prompt
from .query import group_values
from .source import DataSource

logger = logging.getLogger(__name__)
_LLM_FAILURES = (ErpError, requests.RequestException, ValueError, KeyError, TypeError)


@dataclass(frozen=True)
class Answer:
    plan: dict
    data: dict[str, list[dict]]
    presentation: dict
    truncated: tuple[str, ...] = field(default_factory=tuple)


def notice(headline: str, summary: str, *, alert: str | None = None) -> dict:
    return {"headline": headline, "summary": summary, "key_findings": [], "kpis": [],
            "charts": [], "tables": [], "alert": alert}


class AnswerPipeline:
    def __init__(self, pack: Pack, source: DataSource, llm: LLMClient):
        self._pack = pack
        self._source = source
        self._llm = llm
        self._planner_prompt = planner_prompt(pack)
        self._presenter_prompt = presenter_prompt(pack)

    def answer(self, install_id: str | None, question: str) -> Answer:
        plan = self.plan(question)
        a = self._pack.assistant
        if plan.get("intent") == C.INTENT_OUT_OF_SCOPE or not plan["endpoints"]:
            return Answer(plan, {}, notice(a.out_of_scope_headline, plan.get("explanation") or a.out_of_scope_summary))
        try:
            data, truncated = self._source.fetch_many(install_id, plan["endpoints"])
        except ErpError as exc:
            return Answer(plan, {}, notice(f"Couldn't read {self._pack.label}", exc.message, alert=exc.message))
        return Answer(plan, data, self.present(question, self.summarise(data, plan)), truncated)

    def plan(self, question: str) -> dict:
        a = self._pack.assistant
        try:
            result = self._llm.complete_json(self._planner_prompt, f"Question: {question}")
            result["endpoints"] = [e for e in result.get("endpoints", []) if e in self._pack.entities][:C.MAX_PLANNER_ENDPOINTS]
            if not result["endpoints"] and result.get("intent") != C.INTENT_OUT_OF_SCOPE:
                result["endpoints"] = list(a.fallback_endpoints)
            return result
        except _LLM_FAILURES as exc:
            logger.warning("Planner failed, using fallback plan: %s", exc)
            return {"endpoints": list(a.fallback_endpoints), "formula": "", "intent": C.INTENT_GENERAL,
                    "filters": {}, "explanation": a.fallback_summary}

    def present(self, question: str, summary: str) -> dict:
        a = self._pack.assistant
        try:
            result = self._llm.complete_json(self._presenter_prompt, f"Question: {question}\n\nData summary:\n{summary}")
            result.setdefault("key_findings", [])
            result.setdefault("tables", [])
            return result
        except _LLM_FAILURES as exc:
            logger.warning("Presenter failed, using fallback presentation: %s", exc)
            return notice(a.fallback_headline, a.fallback_summary)

    def summarise(self, data: dict[str, list[dict]], plan: dict) -> str:
        a = self._pack.assistant
        lines = [f"Intent: {plan.get('intent', 'unknown')}", f"Formula applied: {plan.get('formula', '')}"]
        lines += [f"{self._pack.entities[name].label}: {len(rows)} records" for name, rows in data.items()]
        for name, value in evaluate_all(self._pack, a.summary_metrics, data).items():
            if value is not None:
                lines.append(f"{self._pack.metrics[name].label}: {format_metric(self._pack, name, value)}")
        for item in a.summary_breakdowns:
            rows = data.get(item["entity"])
            if rows:
                grouped = group_values(rows, group_by=item["group_by"], agg=C.AGG_COUNT) or {}
                counts = {k: int(v) for k, v in grouped.items()}
                lines.append(f"{self._pack.entities[item['entity']].label} by {item['group_by']}: {counts}")
        return "\n".join(lines)
