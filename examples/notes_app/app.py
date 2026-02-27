"""
notes_app -- Ask DIANA Extension.
"""

import os
import logging

from dotenv import load_dotenv

load_dotenv()

from askdiana import ExtensionApp

logging.basicConfig(level=logging.INFO)

app = ExtensionApp("notes_app")


@app.flask.route("/webhooks/install", methods=["POST"])
def on_install():
    from flask import request, jsonify
    app.verify_request()

    body = request.get_json()
    install_id = body["data"]["install_id"]

    # Register and apply all discovered models
    app.setup_models(install_id, version="1.0.0")

    return jsonify({"ok": True}), 200


@app.flask.route("/webhooks/uninstall", methods=["POST"])
def on_uninstall():
    from flask import request, jsonify
    app.verify_request()
    return jsonify({"ok": True}), 200


@app.flask.route("/ui")
def extension_ui():
    from flask import send_from_directory
    return send_from_directory(
        os.path.join(os.path.dirname(__file__), "templates"),
        "index.html",
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(port=port, debug=False)
