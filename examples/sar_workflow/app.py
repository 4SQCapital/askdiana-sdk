"""
SAR Workflow — Suspicious Activity Report Extension for Ask DIANA

Post-conversation workflow that generates a pre-populated SAR form
from the analyst's compliance review conversation.

Run:
    askdiana dev --port 5005
"""

import os
import sys
import logging

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from flask import request, jsonify
from askdiana import ExtensionApp

from sar_service import SarInvokeService

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# --- App setup ---
app = ExtensionApp(__name__, auto_discover=False)

# --- Invoke Service (post-conversation workflow) ---
sar_invoke = SarInvokeService(app)


# ================================================================
# Webhook Handlers
# ================================================================

@app.flask.route("/webhooks/install", methods=["POST"])
def on_install():
    """Handle extension.installed."""
    app.verify_request()
    body = request.get_json()
    data = body.get("data", {})
    install_id = data.get("install_id")
    logger.info(f"SAR Workflow installed: {install_id}")
    return jsonify({"ok": True}), 200


@app.flask.route("/webhooks/uninstall", methods=["POST"])
def on_uninstall():
    """Handle extension.uninstalled."""
    app.verify_request()
    body = request.get_json()
    install_id = body.get("data", {}).get("install_id")
    if install_id:
        logger.info(f"SAR Workflow uninstalled: {install_id}")
    return jsonify({"ok": True}), 200


@app.flask.route("/webhooks/events", methods=["POST"])
def on_event():
    """Handle general events."""
    app.verify_request()
    body = request.get_json()
    logger.info(f"Event: {body.get('event')}")
    return jsonify({"ok": True}), 200


# ================================================================
# Health Check
# ================================================================

@app.flask.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "extension": "sar-workflow",
    }), 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5005))
    app.run(port=port, debug=True)
