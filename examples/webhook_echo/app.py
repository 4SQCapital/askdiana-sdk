"""
Webhook Echo — the simplest possible Ask DIANA extension.

Receives any webhook event, logs the payload, and returns 200.
Great for testing that your webhook endpoint is reachable.

Run:
    export ASKDIANA_API_KEY="askd_your_key"
    python app.py

Then expose via ngrok for testing:
    ngrok http 5001
"""

import os
import json
import logging
import sys

from flask import Flask, request, jsonify

# Allow importing askdiana from the SDK root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))
from askdiana import verify_bearer_token

app = Flask(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
logger = logging.getLogger(__name__)

API_KEY = os.environ.get("ASKDIANA_API_KEY", "")


@app.route("/webhooks", methods=["POST"])
def handle_webhook():
    """Receive and log any webhook event from Ask DIANA."""
    # Verify Bearer token
    try:
        verify_bearer_token(
            authorization_header=request.headers.get("Authorization", ""),
            expected_key=API_KEY,
        )
        logger.info("Bearer token verified OK")
    except ValueError as e:
        logger.warning(f"Verification failed: {e}")
        return jsonify({"error": str(e)}), 401

    event = request.headers.get("X-AskDiana-Event", "unknown")
    body = request.get_json(silent=True) or {}

    logger.info(f"Event: {event}")
    logger.info(f"Payload:\n{json.dumps(body, indent=2)}")

    return jsonify({"received": True, "event": event}), 200


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"ok": True}), 200


if __name__ == "__main__":
    app.run(port=5001, debug=True)
