"""
Webhook Echo — the simplest possible Ask DIANA extension.

Receives any webhook event, logs the payload, and returns 200.
Great for testing that your webhook endpoint is reachable.

Run:
    export WEBHOOK_SIGNING_SECRET="your-secret"
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
from askdiana import verify_webhook, WebhookVerificationError

app = Flask(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
logger = logging.getLogger(__name__)

WEBHOOK_SECRET = os.environ.get("WEBHOOK_SIGNING_SECRET", "")


@app.route("/webhooks", methods=["POST"])
def handle_webhook():
    """Receive and log any webhook event from Ask DIANA."""
    # Verify signature
    try:
        verify_webhook(
            request_body=request.get_data(),
            signature_header=request.headers.get("X-AskDiana-Signature", ""),
            secret=WEBHOOK_SECRET,
            timestamp_header=request.headers.get("X-AskDiana-Delivery-Timestamp"),
        )
        logger.info("Signature verified OK")
    except WebhookVerificationError as e:
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
