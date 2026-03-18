"""
Base class for building AI chat extensions.

Chat extensions add custom AI models (Gemini, OpenAI, local LLMs, etc.)
as chat modes in Ask DIANA.  ``ChatService`` provides a single abstract
method ``respond()`` that receives the user's message and conversation
history, and returns the AI response text.

Usage::

    from askdiana import ChatService

    class GeminiChatService(ChatService):
        def respond(self, install_id, message, history=None, **kwargs):
            import google.generativeai as genai
            genai.configure(api_key=self.get_api_key(install_id))
            model = genai.GenerativeModel("gemini-2.0-flash")
            response = model.generate_content(message)
            return response.text

    app = ExtensionApp(__name__, auto_discover=False)
    svc = GeminiChatService(app.client)
    svc.register_routes(app)
"""

import logging
from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .client import AskDianaClient
    from .app import ExtensionApp

logger = logging.getLogger(__name__)


class ChatService:
    """Base class for AI chat extensions.

    Subclasses must implement:

    - :meth:`respond` — Process a message and return AI response text.

    Optional overrides:

    - :meth:`on_install` — Called when the extension is installed.
    - :meth:`on_uninstall` — Called when the extension is uninstalled.
    """

    def __init__(self, client: "AskDianaClient"):
        self.client = client

    # ------------------------------------------------------------------ #
    # Abstract method — subclass MUST implement                           #
    # ------------------------------------------------------------------ #

    def respond(
        self,
        install_id: str,
        message: str,
        history: Optional[List[Dict[str, str]]] = None,
        chat_id: Optional[str] = None,
        **kwargs: Any,
    ) -> str:
        """Process a user message and return the AI response.

        Args:
            install_id: The install UUID (identifies the user + extension).
            message: The user's message text.
            history: Recent conversation history as a list of
                ``{"role": "user"|"ai", "content": "..."}`` dicts.
            chat_id: Optional Ask DIANA chat UUID for context.
            **kwargs: Additional data passed by the proxy.

        Returns:
            The AI response text (string).
        """
        raise NotImplementedError("Subclasses must implement respond()")

    # ------------------------------------------------------------------ #
    # Optional hooks                                                       #
    # ------------------------------------------------------------------ #

    def on_install(self, install_id: str, data: Dict[str, Any]) -> None:
        """Called when a user installs the extension.  Override to perform setup."""
        pass

    def on_uninstall(self, install_id: str, data: Dict[str, Any]) -> None:
        """Called when a user uninstalls the extension.  Override to clean up."""
        pass

    # ------------------------------------------------------------------ #
    # Helpers                                                              #
    # ------------------------------------------------------------------ #

    def get_config(self, install_id: str, key: str, default: Any = None) -> Any:
        """Read a config value from the extension data storage."""
        try:
            result = self.client.get_data(install_id, "config", key)
            return result.get("data", {}).get("value", default)
        except Exception:
            return default

    def set_config(self, install_id: str, key: str, value: Any) -> None:
        """Write a config value to the extension data storage."""
        self.client.set_data(install_id, "config", key, value)

    def get_api_key(self, install_id: str) -> Optional[str]:
        """Convenience method to read the extension's stored API key."""
        return self.get_config(install_id, "api_key")

    def store_conversation(
        self,
        install_id: str,
        chat_id: str,
        message: str,
        response: str,
    ) -> None:
        """Optionally store conversation in extension's own data storage."""
        import uuid
        entry_id = str(uuid.uuid4())
        self.client.set_data(install_id, "conversations", entry_id, {
            "chat_id": chat_id,
            "message": message,
            "response": response,
        })

    # ------------------------------------------------------------------ #
    # Route registration                                                   #
    # ------------------------------------------------------------------ #

    def register_routes(
        self,
        ext_app: "ExtensionApp",
        verify_signature: bool = True,
    ) -> None:
        """Register the chat respond route on the ExtensionApp.

        Wires up:
        - ``POST /api/chat`` → :meth:`respond`

        Args:
            ext_app: The ExtensionApp instance.
            verify_signature: If True, verify ``Authorization: Bearer`` token.
        """
        from flask import request as flask_request, jsonify as flask_jsonify
        from functools import wraps

        svc = self
        _ext_app = ext_app

        def _apply_base_url(data):
            """If the Ask backend passed askdiana_base_url, update the client."""
            base_url = None
            if isinstance(data, dict):
                base_url = data.pop("askdiana_base_url", None)
            if base_url:
                svc.client.base_url = base_url.rstrip("/")

        def _require_signature(f):
            @wraps(f)
            def wrapper(*args, **kwargs):
                if not verify_signature:
                    return f(*args, **kwargs)
                try:
                    _ext_app.verify_request()
                except Exception as e:
                    logger.warning("Bearer token verification failed: %s", e)
                    return flask_jsonify({"error": "Unauthorized"}), 401
                return f(*args, **kwargs)
            return wrapper

        @ext_app.flask.route("/api/chat", methods=["POST"])
        @_require_signature
        def _chat_respond():
            data = flask_request.get_json() or {}
            _apply_base_url(data)

            install_id = data.get("install_id", "")
            message = data.get("message", "")
            history = data.get("history", [])
            chat_id = data.get("chat_id")

            if not install_id or not message:
                logger.warning("[CHAT] Missing install_id or message in request")
                return flask_jsonify({"error": "install_id and message required"}), 400

            logger.debug(
                "[CHAT] Incoming request: install_id=%s chat_id=%s message_len=%d history_len=%d",
                install_id, chat_id, len(message), len(history),
            )

            try:
                response_text = svc.respond(
                    install_id=install_id,
                    message=message,
                    history=history,
                    chat_id=chat_id,
                )
                logger.debug(
                    "[CHAT] Response generated: install_id=%s response_len=%d",
                    install_id, len(response_text) if response_text else 0,
                )
                return flask_jsonify({"response": response_text}), 200
            except Exception as e:
                logger.error("[CHAT] Respond error for install_id=%s: %s", install_id, e, exc_info=True)
                return flask_jsonify({"error": str(e)}), 500

        logger.info(
            "ChatService routes registered: POST /api/chat"
        )
