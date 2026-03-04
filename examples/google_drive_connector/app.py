"""
Google Drive Connector — Ask DIANA Marketplace Extension

A standalone Flask app that:
1. Receives install/uninstall webhooks from Ask DIANA
2. Uses the developer's Google API key (server-side env var) to access Drive
3. Lists files from Google Drive for the user
4. Downloads files and uploads them to Ask DIANA via the Extension API

Uses the SDK's ExtensionApp, ConnectorService, and Data API.

Run:
    export ASKDIANA_API_KEY="askd_your_key"
    export ASKDIANA_BASE_URL="https://app.askdiana.ai"
    export WEBHOOK_SIGNING_SECRET="your-secret"
    export GOOGLE_API_KEY="AIzaSy..."
    python app.py
"""

import os
import sys
import logging

# Import SDK from parent directory
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

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


# ================================================================
# Webhook Handlers
# ================================================================

@app.flask.route("/webhooks/install", methods=["POST"])
def on_install():
    """Handle extension.installed — set up schema."""
    app.verify_request()

    body = request.get_json()
    install_id = body["data"]["install_id"]

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
# API Endpoints
# ================================================================

@app.flask.route("/api/files", methods=["GET"])
def api_list_files():
    """List files from Google Drive.

    Query params:
        install_id (required): The extension install UUID.
        folder_id (optional): Google Drive folder ID to list from.
        page_token (optional): Pagination token.
    """
    install_id = request.args.get("install_id")
    if not install_id:
        return jsonify({"error": "install_id required"}), 400

    try:
        result = drive.list_files(
            install_id=install_id,
            folder_id=request.args.get("folder_id"),
            page_token=request.args.get("page_token"),
        )
        return jsonify({"success": True, **result}), 200

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"List files error: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.flask.route("/api/sync", methods=["POST"])
def sync_file():
    """Download a file from Google Drive and upload to Ask DIANA.

    Request body::

        {
            "install_id": "uuid",
            "file_id": "google_drive_file_id"
        }
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "JSON body required"}), 400

    install_id = data.get("install_id")
    file_id = data.get("file_id")

    if not install_id or not file_id:
        return jsonify({"error": "install_id and file_id required"}), 400

    try:
        result = drive.sync_file(install_id=install_id, file_id=file_id)
        return jsonify(result), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Sync error: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5004))
    app.run(port=port, debug=True)
