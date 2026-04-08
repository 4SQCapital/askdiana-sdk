"""
SAR Invoke Service — Post-conversation workflow handler.

When the platform triggers this extension at the end of a conversation,
it stores the conversation context and redirects the user to the SAR
form UI, pre-populated with extracted details.
"""

import os
import json
import uuid
import logging
from datetime import datetime

from flask import request as flask_request, jsonify, render_template, url_for

logger = logging.getLogger(__name__)

# In-memory store for demo purposes. In production this would use
# the AskDiana data API (client.set_data / client.get_data).
_pending_reports = {}


class SarInvokeService:
    """Handles POST /api/invoke and GET /ui for the SAR form."""

    def __init__(self, ext_app):
        self._app = ext_app
        self._register_routes()

    def _register_routes(self):

        @self._app.flask.route("/api/invoke", methods=["POST"])
        def _invoke():
            self._app.verify_request()
            body = flask_request.get_json() or {}
            return self._handle_invoke(body)

        @self._app.flask.route("/ui")
        def _ui():
            return self._serve_ui()

        @self._app.flask.route("/api/sar/submit", methods=["POST"])
        def _submit():
            return self._handle_submit()

    # ------------------------------------------------------------------
    # Invoke handler — receives conversation context from platform
    # ------------------------------------------------------------------

    def _handle_invoke(self, body: dict):
        install_id = body.get("install_id", "")
        params = body.get("parameters", {})
        last_response = body.get("last_response", "")
        title = body.get("title", "")
        conversation = body.get("conversation", [])

        # Extract relevant details from the conversation
        context = self._extract_context(last_response, conversation)
        context["priority"] = params.get("priority", "high")

        # Store for the UI to pick up
        report_id = str(uuid.uuid4())[:8]
        _pending_reports[report_id] = context

        logger.info(
            "SAR invoke: install=%s report=%s subject=%s",
            install_id, report_id, context.get("subject_name", "unknown"),
        )

        # Return redirect to the form UI with the report context
        base_url = flask_request.host_url.rstrip("/")
        form_url = f"{base_url}/ui?report_id={report_id}&install_id={install_id}"

        return jsonify({
            "result_type": "redirect",
            "url": form_url,
        }), 200

    # ------------------------------------------------------------------
    # UI handler — serves the SAR form
    # ------------------------------------------------------------------

    def _serve_ui(self):
        report_id = flask_request.args.get("report_id", "")
        install_id = flask_request.args.get("install_id", "")

        # Load context from invoke, or fall back to mock data for demo
        context = _pending_reports.get(report_id, self._mock_context())

        return render_template(
            "index.html",
            context_json=json.dumps(context),
            install_id=install_id,
        )

    # ------------------------------------------------------------------
    # Submit handler
    # ------------------------------------------------------------------

    def _handle_submit(self):
        body = flask_request.get_json() or {}
        ref = body.get("reference", "unknown")
        logger.info("SAR submitted: %s", ref)

        # In production: persist via client.set_data or forward to
        # the company's compliance system.
        return jsonify({"ok": True, "reference": ref}), 200

    # ------------------------------------------------------------------
    # Context extraction from conversation
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_context(last_response: str, conversation: list) -> dict:
        """Pull structured fields from the AI's last response and
        conversation history. In production this could use an LLM call
        to extract entities; for now we use the last response as the
        narrative and pull any document references from the conversation."""

        # Collect document references mentioned in the conversation
        docs = []
        for msg in conversation:
            content = msg.get("content", "")
            # Simple heuristic: look for file-like references
            for word in content.split():
                if "." in word and word.split(".")[-1].lower() in (
                    "pdf", "docx", "xlsx", "csv", "png", "jpg", "msg"
                ):
                    clean = word.strip("(),;:\"'")
                    if clean not in docs:
                        docs.append(clean)

        return {
            "subject_name": "",
            "account_reference": "",
            "activity_start_date": "",
            "activity_end_date": "",
            "transaction_amounts": "",
            "currency": "USD",
            "activity_type": "",
            "narrative": last_response[:2000] if last_response else "",
            "supporting_docs": docs,
        }

    @staticmethod
    def _mock_context() -> dict:
        """Demo / standalone mock data — used when the form is opened
        directly (not via a real invoke from the platform)."""
        return {
            "subject_name": "Meridian Holdings Ltd.",
            "account_reference": "TXN-4820193-MHL",
            "activity_start_date": "2026-01-15",
            "activity_end_date": "2026-03-28",
            "transaction_amounts": "$142,500.00; $89,300.00; $67,200.00",
            "currency": "USD",
            "activity_type": "Unusual Transaction Pattern",
            "narrative": (
                "Multiple high-value cross-border transfers identified between "
                "Meridian Holdings Ltd. (Singapore) and three shell entities in "
                "jurisdictions with weak AML controls. Transactions were split "
                "into amounts just below the $150,000 reporting threshold over "
                "a 10-week period. Funds were routed through correspondent "
                "accounts in two intermediary banks before settling in a newly "
                "opened account with no prior transaction history. Pattern "
                "consistent with layering and structuring to evade detection."
            ),
            "supporting_docs": [
                "Transaction_Ledger_Q1_2026.pdf",
                "KYC_Profile_Meridian_Holdings.docx",
                "SWIFT_Messages_Jan-Mar_2026.csv",
                "Sanctions_Screening_Result.pdf",
            ],
            "priority": "high",
        }
