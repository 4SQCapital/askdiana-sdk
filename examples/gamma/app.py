"""
Gamma — Presentation Generator Extension for Ask DIANA

Integrates with Gamma.app to generate beautiful presentations,
documents, and webpages directly from chat messages.

Run:
    askdiana dev --port 5004
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

from gamma_service import GammaChatService, GammaInvokeService

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# --- App setup ---
app = ExtensionApp(__name__, auto_discover=False)

# --- Chat Service (chat mode) ---
gamma = GammaChatService(app.client)
gamma.register_routes(app)

# --- Invoke Service (post-conversation workflow) ---
gamma_invoke = GammaInvokeService(app)


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

    for key in (
        "api_key",
        "format",
        "num_cards",
        "export_format",
        "tone",
        "language",
        "template_mode",
        "template_id",
        "content_amount",
        "logo_url",
        "brand_name",
    ):
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

@app.flask.route("/api/themes", methods=["GET"])
def list_themes():
    """Return workspace themes from Gamma API for the requesting install."""
    app.verify_request()
    install_id = request.args.get("install_id", "")

    api_key = None
    if app.client and install_id:
        try:
            cfg = app.client.get_config(install_id) or {}
            api_key = cfg.get("api_key")
        except Exception:
            pass
    if not api_key:
        api_key = os.environ.get("GAMMA_API_KEY")
    if not api_key:
        return jsonify({"themes": [], "error": "No API key configured"}), 200

    try:
        import requests as _req
        resp = _req.get(
            "https://public-api.gamma.app/v1.0/themes",
            headers={"X-API-KEY": api_key, "Content-Type": "application/json"},
            timeout=10,
        )
        if resp.status_code not in (200, 201):
            return jsonify({"themes": [], "error": f"Gamma API {resp.status_code}"}), 200
        body = resp.json()
        items = body if isinstance(body, list) else (body.get("themes") or body.get("data") or [])
        themes = []
        for item in items:
            tid = str(item.get("id") or item.get("themeId") or "").strip()
            name = str(item.get("name") or item.get("title") or tid).strip()
            if tid:
                themes.append({"value": tid, "label": name})
        return jsonify({"themes": themes}), 200
    except Exception as e:
        logger.error("Failed to fetch Gamma themes: %s", e)
        return jsonify({"themes": [], "error": str(e)}), 200


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
