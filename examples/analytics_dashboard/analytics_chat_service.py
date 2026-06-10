"""Chat service for the Analytics Dashboard extension.

Lets users ask questions about the dashboard's sales/usage data directly
from the Ask DIANA chat box (the "chat mode" feature).

Responses are returned as ``rich_response`` JSON (the same block schema
``RichResponseRenderer`` on the host renders for workflow results), so
answers show up as formatted cards/tables instead of plain text.
"""

import json
import logging

from askdiana import ChatService

from analytics_data import (
    KPIS,
    REVENUE_SERIES,
    CATEGORY_BREAKDOWN,
    TOP_PRODUCTS,
    GOALS,
    RECENT_TRANSACTIONS,
)

logger = logging.getLogger(__name__)

HELP_ITEMS = [
    "revenue (e.g. \"what's our revenue?\")",
    "active users",
    "conversion rate",
    "average order value",
    "top products",
    "category breakdown",
    "goals / progress",
    "recent transactions",
]


def _rich(*blocks):
    """Wrap blocks in the rich_response envelope the host renders."""
    return json.dumps({"type": "rich_response", "blocks": list(blocks)})


def _text(content, style=None):
    block = {"type": "text", "content": content}
    if style:
        block["style"] = style
    return block


def _card(title, body, accent=None):
    block = {"type": "card", "title": title, "body": body}
    if accent:
        block["accent"] = accent
    return block


def _table(headers, rows):
    return {"type": "table", "headers": headers, "rows": rows}


def _list(items):
    return {"type": "list", "items": items}


class AnalyticsChatService(ChatService):
    """Answers questions about the mock sales/usage dataset."""

    def respond(self, install_id, message, history=None, chat_id=None, **kwargs):
        text = (message or "").lower()

        if any(w in text for w in ["help", "what can you", "what do you"]):
            return self._help()

        if "revenue" in text:
            return self._revenue_summary()

        if "user" in text:
            return self._kpi_card(KPIS["active_users"])

        if "conversion" in text:
            return self._kpi_card(KPIS["conversion_rate"])

        if "order value" in text or "aov" in text:
            return self._kpi_card(KPIS["avg_order_value"])

        if "product" in text or "best seller" in text or "top sell" in text:
            return self._top_products_summary()

        if "categor" in text:
            return self._category_summary()

        if "goal" in text or "target" in text or "progress" in text:
            return self._goals_summary()

        if "transaction" in text or "order" in text:
            return self._transactions_summary()

        return self._help(
            intro="I'm the Analytics Assistant for this dashboard. Ask me about:"
        )

    def _help(self, intro="I can answer questions about the analytics dashboard. Try asking about:"):
        return _rich(_text(intro), _list(HELP_ITEMS))

    def _kpi_card(self, kpi):
        return _rich(_card(kpi["label"], f"**{kpi['value']}** ({kpi['delta']} vs last month)"))

    def _revenue_summary(self):
        kpi = KPIS["revenue"]
        latest = REVENUE_SERIES[-1]
        previous = REVENUE_SERIES[-2]
        return _rich(
            _card(
                "Revenue",
                f"**{kpi['value']}** ({kpi['delta']} vs last month)\n\n"
                f"{latest['month']}: ${latest['revenue']:,} from {latest['orders']} orders, "
                f"up from ${previous['revenue']:,} in {previous['month']}.",
            ),
            _table(
                ["Month", "Revenue", "Orders"],
                [[p["month"], f"${p['revenue']:,}", str(p["orders"])] for p in REVENUE_SERIES[-6:]],
            ),
        )

    def _top_products_summary(self):
        return _rich(
            _text("Top products by revenue:"),
            _table(
                ["Product", "Units sold", "Revenue"],
                [
                    [p["name"], f"{p['units_sold']:,}", f"${p['revenue']:,}"]
                    for p in TOP_PRODUCTS
                ],
            ),
        )

    def _category_summary(self):
        return _rich(
            _text("Sales by category:"),
            _table(
                ["Category", "Share"],
                [[c["name"], f"{c['value']}%"] for c in CATEGORY_BREAKDOWN],
            ),
        )

    def _goals_summary(self):
        rows = []
        for g in GOALS:
            unit = g["unit"]
            if unit == "$":
                value, target = f"${g['value']:,.0f}", f"${g['target']:,.0f}"
            elif unit == "%":
                value, target = f"{g['value']}%", f"{g['target']}%"
            else:
                value, target = f"{g['value']:,}", f"{g['target']:,}"
            pct = round(g["value"] / g["target"] * 100)
            rows.append([g["label"], value, target, f"{pct}%"])
        return _rich(
            _text("Progress toward this month's goals:"),
            _table(["Goal", "Current", "Target", "Progress"], rows),
        )

    def _transactions_summary(self):
        total = sum(t["amount"] for t in RECENT_TRANSACTIONS)
        pending = sum(1 for t in RECENT_TRANSACTIONS if t["status"] == "pending")
        refunded = sum(1 for t in RECENT_TRANSACTIONS if t["status"] == "refunded")
        return _rich(
            _text(
                f"There are {len(RECENT_TRANSACTIONS)} recent transactions totaling "
                f"${total:,.2f} ({pending} pending, {refunded} refunded)."
            ),
            _table(
                ["Transaction", "Customer", "Amount", "Status", "Date"],
                [
                    [t["id"], t["customer"], f"${t['amount']:,.2f}", t["status"], t["date"]]
                    for t in RECENT_TRANSACTIONS
                ],
            ),
        )
