"""
analytics_dashboard -- Ask DIANA Extension.
"""

import os
import logging

from dotenv import load_dotenv
from flask import send_from_directory, request, jsonify

load_dotenv()

from askdiana import ExtensionApp

from analytics_chat_service import AnalyticsChatService

logging.basicConfig(level=logging.INFO)

app = ExtensionApp("analytics_dashboard")

# --- Chat mode: POST /api/chat ---
analytics_chat = AnalyticsChatService(app.client)
analytics_chat.register_routes(app)


@app.flask.route("/webhooks/install", methods=["POST"])
def on_install():
    app.verify_request()
    body = request.get_json()
    install_id = body["data"]["install_id"]
    app.setup_models(install_id, version="1.0.0")
    return jsonify({"ok": True}), 200


@app.flask.route("/webhooks/uninstall", methods=["POST"])
def on_uninstall():
    app.verify_request()
    return jsonify({"ok": True}), 200


@app.flask.route("/ui")
def extension_ui():
    return send_from_directory(
        os.path.join(os.path.dirname(__file__), "static"), "index.html",
    )


@app.flask.route("/ui/<path:filename>")
def extension_ui_assets(filename):
    return send_from_directory(
        os.path.join(os.path.dirname(__file__), "static"), filename,
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    app.run(port=port, debug=False)
