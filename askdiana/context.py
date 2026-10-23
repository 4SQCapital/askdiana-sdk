"""
Who is using the extension, and in which persona.

Ask DIANA signs a short-lived context (a JWT, HS256) with the extension's own
API key and sends it with a user's requests:

- views get it in ``init.context`` and send it back in the
  ``X-AskDiana-Context`` header (``bridge.fetch`` in askdiana-ui does this);
- chat gets it in the ``/api/chat`` body as ``context``.

Usage::

    from askdiana.context import request_context

    @app.route("/api/cases/<case_id>/close", methods=["POST"])
    def close(case_id):
        ctx = request_context(required=True)
        if ctx.persona is None or ctx.persona.name != "AML Officer":
            return {"error": "Only the AML Officer may close this case"}, 403
        docs = app.client.with_context(ctx).search_documents(ctx.install_id, "closure authority")

Trust the persona only from a verified context, never from a value the browser
sends some other way. On an older platform there is no context:
``request_context()`` returns None, so keep a fallback.
"""

import base64
import binascii
import hashlib
import hmac
import json
import os
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional

HEADER = "X-AskDiana-Context"
ISSUER = "askdiana"
LEEWAY_SECONDS = 30

_G_KEY = "askdiana_context"


class ContextError(ValueError):
    """The context is missing, malformed, forged, expired or for another install."""


@dataclass(frozen=True)
class Persona:
    id: str
    name: str
    kind: Optional[str] = None

    @property
    def admin_managed(self) -> bool:
        """Set up by a tenant admin. Map roles only from these: any user may name their own persona anything."""
        return self.kind == "admin_managed"


@dataclass(frozen=True)
class RequestContext:
    token: str
    user_id: str
    tenant_id: str
    install_id: str
    extension_id: str
    name: Optional[str]
    email: Optional[str]
    persona: Optional[Persona]
    expires_at: int


def _b64decode(part: str) -> bytes:
    return base64.urlsafe_b64decode(part + "=" * (-len(part) % 4))


def verify_context(
    token: str,
    *,
    install_id: str,
    api_key: Optional[str] = None,
    now: Optional[float] = None,
) -> RequestContext:
    """Check a context token and return what it says.

    Args:
        token: The token from ``X-AskDiana-Context`` or the chat body.
        install_id: The install this request is for; a token for another install is rejected.
        api_key: The extension's API key. Defaults to ``ASKDIANA_API_KEY``.

    Raises:
        ContextError: If the token can't be trusted.
    """
    key = api_key or os.environ.get("ASKDIANA_API_KEY", "")
    if not key:
        raise ContextError("No API key to verify the context with")
    try:
        header_b64, payload_b64, signature_b64 = str(token).split(".")
        header = json.loads(_b64decode(header_b64))
        claims: Dict[str, Any] = json.loads(_b64decode(payload_b64))
        signature = _b64decode(signature_b64)
    except (ValueError, binascii.Error) as exc:
        raise ContextError("Malformed context") from exc

    if header.get("alg") != "HS256":
        raise ContextError("Unsupported context algorithm")
    expected = hmac.new(key.encode(), f"{header_b64}.{payload_b64}".encode(), hashlib.sha256).digest()
    if not hmac.compare_digest(expected, signature):
        raise ContextError("Context signature does not match")
    if claims.get("iss") != ISSUER:
        raise ContextError("Context was not issued by Ask DIANA")
    if str(claims.get("aud")) != str(install_id):
        raise ContextError("Context is for another install")
    expires_at = claims.get("exp")
    current = time.time() if now is None else now
    if not isinstance(expires_at, (int, float)) or expires_at + LEEWAY_SECONDS < current:
        raise ContextError("Context has expired")

    persona = claims.get("persona")
    return RequestContext(
        token=str(token),
        user_id=str(claims.get("sub")),
        tenant_id=str(claims.get("tid")),
        install_id=str(claims.get("aud")),
        extension_id=str(claims.get("ext")),
        name=claims.get("name"),
        email=claims.get("email"),
        persona=Persona(id=str(persona["id"]), name=str(persona.get("name") or ""), kind=persona.get("kind"))
        if persona
        else None,
        expires_at=int(expires_at),
    )


def request_context(
    api_key: Optional[str] = None,
    *,
    required: bool = False,
) -> Optional[RequestContext]:
    """The verified context of the current Flask request, or None when there is none.

    Reads ``X-AskDiana-Context``, or ``context`` in a JSON body (chat). The
    install comes from ``install_id`` in the query or body, or ``X-Install-Id``.
    The result is cached for the request.

    Raises:
        ContextError: If a context was sent but can't be trusted, or if
            ``required`` and none was sent.
    """
    from flask import g, request

    if _G_KEY in g:
        cached = g.get(_G_KEY)
        if cached is None and required:
            raise ContextError("This request has no Ask DIANA context")
        return cached

    body = request.get_json(silent=True) if request.is_json else None
    body = body if isinstance(body, dict) else {}
    token = request.headers.get(HEADER) or body.get("context")
    ctx = None
    if token:
        install_id = (
            request.args.get("install_id")
            or body.get("install_id")
            or request.headers.get("X-Install-Id")
        )
        if not install_id:
            raise ContextError("No install_id to check the context against")
        ctx = verify_context(token, install_id=install_id, api_key=api_key)
    setattr(g, _G_KEY, ctx)
    if ctx is None and required:
        raise ContextError("This request has no Ask DIANA context")
    return ctx
