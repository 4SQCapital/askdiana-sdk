"""
Gamma — Presentation Generator Extension for Ask DIANA

Integrates with Gamma.app to generate beautiful presentations,
documents, and webpages directly from chat messages.

Run:
    export ASKDIANA_API_KEY="askd_your_key"
    export ASKDIANA_BASE_URL="https://app.askdiana.ai"
    export GAMMA_API_KEY="your-gamma-api-key"
    python app.py
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

from gamma_service import GammaChatService

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# --- App setup ---
app = ExtensionApp(__name__, auto_discover=False)

# --- Chat Service ---
gamma = GammaChatService(app.client)
gamma.register_routes(app)


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
    config = data.get("config", {})

    for key in ("api_key", "format", "num_cards", "export_format", "tone", "language"):
        if config.get(key):
            gamma.set_config(install_id, key, config[key])

    logger.info(f"Gamma installed: {install_id}")
    return jsonify({"ok": True}), 200


@app.flask.route("/webhooks/uninstall", methods=["POST"])
def on_uninstall():
    """Handle extension.uninstalled."""
    app.verify_request()
    body = request.get_json()
    install_id = body.get("data", {}).get("install_id")
    if install_id:
        logger.info(f"Gamma uninstalled: {install_id}")
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
    has_key = bool(os.environ.get("GAMMA_API_KEY"))
    return jsonify({
        "status": "ok",
        "extension": "gamma",
        "gamma_key_configured": has_key,
    }), 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5004))
    app.run(port=port, debug=True)
