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

import json
import os
import logging

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import jwt
import requests as http_requests
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


# ================================================================
# Google Cross-Account Protection (RISC) Webhook
# ================================================================

_RISC_CONFIG_URL = "https://accounts.google.com/.well-known/risc-configuration"
_RISC_REVOKE_EVENTS = {
    "https://schemas.openid.net/secevent/risc/event-type/sessions-revoked",
    "https://schemas.openid.net/secevent/risc/event-type/token-revoked",
    "https://schemas.openid.net/secevent/risc/event-type/account-disabled",
    "https://schemas.openid.net/secevent/risc/event-type/account-purged",
    "https://schemas.openid.net/secevent/oauth/event-type/tokens-revoked",
}


@app.flask.route("/webhooks/risc", methods=["POST"])
def risc_webhook():
    """Google Cross-Account Protection webhook.

    Receives signed Security Event Tokens (SETs) from Google when a
    user's account is compromised or tokens are revoked. We respond by
    disconnecting the affected install so stale tokens are never used.
    """
    token = request.data.decode("utf-8")
    if not token:
        return jsonify({"error": "Empty body"}), 400

    try:
        # Fetch Google's RISC config to get the correct jwks_uri and issuer
        risc_config = http_requests.get(_RISC_CONFIG_URL, timeout=10).json()
        jwks = http_requests.get(risc_config["jwks_uri"], timeout=10).json()

        header = jwt.get_unverified_header(token)
        kid = header.get("kid")

        # Find matching public key
        public_key = None
        for key in jwks.get("keys", []):
            if key.get("kid") == kid:
                public_key = jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(key))
                break

        if not public_key:
            logger.warning("RISC: unknown key id=%s", kid)
            return jsonify({"error": "Unknown signing key"}), 400

        client_id = os.environ.get("GOOGLE_CLIENT_ID", "")
        payload = jwt.decode(
            token,
            public_key,
            algorithms=["RS256"],
            options={"verify_exp": False},  # security events are historical
            audience=client_id,
            issuer=risc_config["issuer"],
        )

        events = payload.get("events", {})
        logger.info("RISC event received: events=%s", list(events.keys()))

        for event_type, event_data in events.items():
            if event_type in _RISC_REVOKE_EVENTS:
                # Google user ID is nested inside the event subject
                subject = (
                    event_data.get("subject", {}).get("sub")
                    or payload.get("sub")
                )
                logger.warning("RISC: revoking tokens for subject=%s event=%s", subject, event_type)
                if subject:
                    drive.revoke_tokens_for_google_id(subject)
                break

        return "", 202

    except jwt.ExpiredSignatureError:
        logger.warning("RISC: expired token received")
        return jsonify({"error": "Token expired"}), 400
    except jwt.InvalidTokenError as e:
        logger.warning("RISC: invalid token: %s", e)
        return jsonify({"error": "Invalid token"}), 400
    except Exception as e:
        logger.error("RISC webhook error: %s", e, exc_info=True)
        return jsonify({"error": "Internal error"}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5004))
    app.run(port=port, debug=False)
