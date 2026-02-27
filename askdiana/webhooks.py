"""
Webhook signature verification for Ask DIANA extensions.

Ask DIANA signs every webhook delivery with HMAC-SHA256 so your extension
can verify the request is authentic.

Usage::

    from askdiana import verify_webhook, WebhookVerificationError

    @app.route("/webhooks", methods=["POST"])
    def handle_webhook():
        try:
            verify_webhook(
                request_body=request.get_data(),
                signature_header=request.headers["X-AskDiana-Signature"],
                secret=WEBHOOK_SECRET,
                timestamp_header=request.headers.get("X-AskDiana-Delivery-Timestamp"),
            )
        except WebhookVerificationError as e:
            return {"error": str(e)}, 401

        # Process the verified event ...
"""

import hmac
import hashlib
import time
from typing import Optional


class WebhookVerificationError(Exception):
    """Raised when webhook signature verification fails."""


def verify_webhook(
    request_body,
    signature_header: str,
    secret: str,
    tolerance_seconds: Optional[int] = 300,
    timestamp_header: Optional[str] = None,
) -> bool:
    """
    Verify an incoming webhook from Ask DIANA.

    Args:
        request_body: Raw request body (bytes or str).
        signature_header: Value of the ``X-AskDiana-Signature`` header
            (format: ``sha256=<hex_digest>``).
        secret: Your ``WEBHOOK_SIGNING_SECRET``.
        tolerance_seconds: Maximum acceptable age of a webhook in seconds
            (default 5 min).  Set to ``None`` to skip timestamp checking.
        timestamp_header: Value of the ``X-AskDiana-Delivery-Timestamp``
            header (Unix epoch seconds).

    Returns:
        ``True`` when verification passes.

    Raises:
        WebhookVerificationError: If the signature is invalid, the format
            is wrong, or the timestamp is stale.
    """
    # --- Timestamp freshness check ---
    if tolerance_seconds is not None and timestamp_header:
        try:
            ts = int(timestamp_header)
            if abs(time.time() - ts) > tolerance_seconds:
                raise WebhookVerificationError(
                    "Webhook timestamp too old (possible replay)"
                )
        except (ValueError, TypeError):
            raise WebhookVerificationError("Invalid timestamp header")

    # --- Signature format ---
    if not signature_header or not signature_header.startswith("sha256="):
        raise WebhookVerificationError(
            "Invalid signature format — expected 'sha256=<hex>'"
        )
    received_sig = signature_header[7:]

    # --- Compute expected HMAC ---
    body_str = (
        request_body.decode("utf-8")
        if isinstance(request_body, (bytes, bytearray))
        else request_body
    )
    expected_sig = hmac.new(
        secret.encode("utf-8"),
        body_str.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(received_sig, expected_sig):
        raise WebhookVerificationError("Signature mismatch")

    return True
