"""
Webhook request verification for Ask DIANA extensions.

Ask DIANA authenticates every webhook delivery and API call with a Bearer
token (the extension's ``ASKDIANA_API_KEY``).  Your extension verifies the
request by comparing the token to its own key.

Usage::

    from askdiana import verify_bearer_token

    @app.route("/webhooks", methods=["POST"])
    def handle_webhook():
        try:
            verify_bearer_token(
                authorization_header=request.headers.get("Authorization", ""),
                expected_key=os.environ["ASKDIANA_API_KEY"],
            )
        except ValueError as e:
            return {"error": str(e)}, 401

        # Process the verified event ...
"""

import hmac


class WebhookVerificationError(Exception):
    """Raised when webhook request verification fails.

    .. deprecated::
        Kept for backwards compatibility.  New code should catch
        ``ValueError`` instead.
    """


def verify_bearer_token(
    authorization_header: str,
    expected_key: str,
) -> bool:
    """Verify an incoming request from Ask DIANA using Bearer token auth.

    Args:
        authorization_header: Value of the ``Authorization`` header
            (format: ``Bearer <token>``).
        expected_key: Your ``ASKDIANA_API_KEY``.

    Returns:
        ``True`` when verification passes.

    Raises:
        ValueError: If the token is missing or does not match.
    """
    if not authorization_header or not authorization_header.startswith("Bearer "):
        raise ValueError(
            "Missing or invalid Authorization header — expected 'Bearer <token>'"
        )

    token = authorization_header[7:]

    if not expected_key:
        raise ValueError("ASKDIANA_API_KEY is not configured")

    if not hmac.compare_digest(token, expected_key):
        raise ValueError("Invalid Bearer token")

    return True


# ------------------------------------------------------------------
# Backwards-compatible alias
# ------------------------------------------------------------------

def verify_webhook(
    request_body=None,
    signature_header: str = "",
    secret: str = "",
    tolerance_seconds=None,
    timestamp_header=None,
    *,
    authorization_header: str = "",
    expected_key: str = "",
) -> bool:
    """Backwards-compatible verification wrapper.

    If *authorization_header* is provided, delegates to Bearer token
    verification.  Otherwise raises ``WebhookVerificationError`` since
    HMAC signing has been removed.

    .. deprecated::
        Use :func:`verify_bearer_token` directly.
    """
    # New-style Bearer auth
    auth = authorization_header or ""
    key = expected_key or secret or ""
    if auth:
        try:
            return verify_bearer_token(auth, key)
        except ValueError as exc:
            raise WebhookVerificationError(str(exc)) from exc

    raise WebhookVerificationError(
        "HMAC webhook signing has been removed. "
        "Ask DIANA now uses Bearer token authentication. "
        "Update your extension to check the Authorization header."
    )
