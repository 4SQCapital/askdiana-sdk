"""
Controller helpers and decorators for extension Flask Blueprints.

Provides:
- ``webhook_required``: decorator that verifies webhook signatures
- ``install_id_required``: decorator that extracts install_id from
  request args or JSON body
"""

import functools
import logging
import os
from typing import Callable, Optional

from flask import g, jsonify, request

from .webhooks import WebhookVerificationError, verify_webhook

logger = logging.getLogger(__name__)


def webhook_required(secret: Optional[str] = None):
    """Decorator that verifies the Ask DIANA webhook signature.

    If verification fails, returns a ``401`` JSON response.

    Args:
        secret: Webhook signing secret.  Falls back to the
            ``WEBHOOK_SIGNING_SECRET`` environment variable.

    Usage::

        @tasks_bp.route("/webhooks/install", methods=["POST"])
        @webhook_required()
        def on_install():
            body = request.get_json()
            ...
    """

    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            signing_secret = secret or os.environ.get("WEBHOOK_SIGNING_SECRET", "")
            try:
                verify_webhook(
                    request_body=request.get_data(),
                    signature_header=request.headers.get("X-AskDiana-Signature", ""),
                    secret=signing_secret,
                    timestamp_header=request.headers.get("X-AskDiana-Delivery-Timestamp"),
                )
            except WebhookVerificationError as exc:
                logger.warning("Webhook verification failed: %s", exc)
                return jsonify({"error": str(exc)}), 401
            return fn(*args, **kwargs)

        return wrapper

    return decorator


def install_id_required(fn: Callable) -> Callable:
    """Decorator that extracts ``install_id`` into ``flask.g.install_id``.

    Checks (in order):

    1. Query parameter ``?install_id=...``
    2. JSON body ``{"data": {"install_id": "..."}}`` (webhook format)
    3. JSON body ``{"install_id": "..."}``

    Returns ``400`` if not found.
    """

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        install_id = request.args.get("install_id")

        if not install_id:
            body = request.get_json(silent=True) or {}
            install_id = body.get("data", {}).get("install_id") or body.get("install_id")

        if not install_id:
            return jsonify({"error": "install_id required"}), 400

        g.install_id = install_id
        return fn(*args, **kwargs)

    return wrapper
