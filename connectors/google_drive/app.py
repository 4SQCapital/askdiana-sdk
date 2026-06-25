"""
Google Drive Connector — Ask DIANA Extension

A standalone Flask app that:
1. Receives install/uninstall webhooks from Ask DIANA
2. Handles Google OAuth on behalf of users
3. Lists files from the user's Google Drive
4. Downloads files and uploads them to Ask DIANA via the Extension API

Run:
    askdiana dev --port 5004
"""

import os
import logging

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from flask import request, jsonify
from askdiana import ExtensionApp

from drive_service import GoogleDriveService

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# --- App setup ---
app = ExtensionApp(__name__, auto_discover=False)

# --- Service ---
drive = GoogleDriveService(app.client)

# Register all connector routes (/api/auth/*, /api/files, /api/sync)
drive.register_routes(app)


@app.flask.route("/api/auth/token", methods=["GET"])
def get_auth_token():
    """Return a valid access token + Picker API key for the Google Picker (frontend use)."""
    install_id = request.args.get("install_id")
    if not install_id:
        return jsonify({"error": "install_id required"}), 400
    try:
        token = drive._get_valid_access_token(install_id)
        api_key = os.environ.get("GOOGLE_PICKER_API_KEY", "")
        return jsonify({"access_token": token, "api_key": api_key})
    except Exception as e:
        logger.warning(f"Failed to get access token for picker: {e}")
        return jsonify({"error": "Not connected"}), 401


# ================================================================
# Webhook Handlers
# ================================================================

@app.flask.route("/webhooks/install", methods=["POST"])
def on_install():
    """Handle extension.installed."""
    app.verify_request()
    body = request.get_json()
    install_id = body["data"]["install_id"]
    logger.info(f"Extension installed: {install_id}")
    return jsonify({"ok": True}), 200


@app.flask.route("/webhooks/uninstall", methods=["POST"])
def on_uninstall():
    """Handle extension.uninstalled — clean up stored tokens."""
    app.verify_request()
    body = request.get_json()
    install_id = body.get("data", {}).get("install_id")
    if install_id:
        try:
            drive.disconnect(install_id)
        except Exception as e:
            logger.warning(f"Failed to clean up tokens on uninstall: {e}")
        logger.info(f"Extension uninstalled: {install_id}")
    return jsonify({"ok": True}), 200


@app.flask.route("/webhooks/events", methods=["POST"])
def on_event():
    """Handle general events."""
    app.verify_request()
    body = request.get_json()
    logger.info(f"Event: {body.get('event')}")
    return jsonify({"ok": True}), 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5004))
    app.run(port=port, debug=False)
