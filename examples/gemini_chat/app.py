"""
Ask Gemini — Ask DIANA AI Chat Extension

A standalone Flask app that:
1. Receives install/uninstall webhooks from Ask DIANA
2. Provides a /api/chat endpoint for chat_respond capability
3. Processes messages through Google Gemini API
4. Stores user API keys in extension data storage

Uses the SDK's ExtensionApp, ChatService, and Data API.

Run:
    askdiana dev --port 5003
"""

import os
import sys
import logging

# Import SDK from parent directory (for development)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

from flask import request, jsonify
from askdiana import ExtensionApp

from gemini_service import GeminiChatService

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# --- App setup ---
app = ExtensionApp(__name__, auto_discover=False)

# --- Chat Service ---
gemini = GeminiChatService(app.client)

# Register chat route: POST /api/chat
gemini.register_routes(app)


# ================================================================
# Webhook Handlers
# ================================================================

@app.flask.route("/webhooks/install", methods=["POST"])
def on_install():
    """Handle extension.installed — store user config."""
    app.verify_request()

    body = request.get_json()
    data = body.get("data", {})
    install_id = data.get("install_id")
    config = data.get("config", {})

    # Store API key and model preference from install config
    if config.get("api_key"):
        gemini.set_config(install_id, "api_key", config["api_key"])
    if config.get("model"):
        gemini.set_config(install_id, "model", config["model"])

    logger.info(f"Extension installed: {install_id}")
    return jsonify({"ok": True}), 200


@app.flask.route("/webhooks/uninstall", methods=["POST"])
def on_uninstall():
    """Handle extension.uninstalled."""
    app.verify_request()

    body = request.get_json()
    install_id = body.get("data", {}).get("install_id")
    if install_id:
        logger.info(f"Extension uninstalled: {install_id}")

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
    """Simple health check endpoint."""
    has_default_key = bool(os.environ.get("GEMINI_API_KEY"))
    return jsonify({
        "status": "ok",
        "extension": "ask-gemini",
        "gemini_key_configured": has_default_key,
    }), 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5003))
    app.run(port=port, debug=True)
