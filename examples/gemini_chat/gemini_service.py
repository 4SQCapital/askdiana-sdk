"""
Gemini Chat Service — Ask DIANA AI Chat Extension

Implements ChatService to add "Ask Gemini" as a chat mode in Ask DIANA.
Uses Google's GenAI SDK to call Gemini models.

The service:
1. Reads the user's API key from extension config (or falls back to env var)
2. Builds conversation context from message history
3. Calls Gemini API and returns the response text
"""

import os
import logging

from askdiana import ChatService

logger = logging.getLogger(__name__)

# Default model — can be overridden per-install via config
DEFAULT_MODEL = "gemini-2.5-flash-lite"


class GeminiChatService(ChatService):
    """Ask Gemini — AI chat extension powered by Google Gemini."""

    def respond(self, install_id, message, history=None, chat_id=None, **kwargs):
        """Process a user message through Gemini and return the response.

        Args:
            install_id: The install UUID (identifies the user).
            message: The user's message text.
            history: Recent conversation history.
            chat_id: Optional Ask DIANA chat UUID.

        Returns:
            The Gemini response text.
        """
        try:
            from google import genai
        except ImportError:
            return (
                "The `google-genai` package is not installed. "
                "Run: pip install google-genai"
            )

        # 1. Get API key — user config first, then developer's default
        api_key = self.get_api_key(install_id)
        if not api_key:
            api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            return (
                "No Gemini API key configured. Please add your API key "
                "in the extension settings, or ask the admin to configure "
                "a default key."
            )

        # 2. Get model preference
        model_name = self.get_config(install_id, "model", DEFAULT_MODEL)

        # 3. Create Gemini client
        client = genai.Client(api_key=api_key)

        # 4. Build conversation contents from history
        contents = []
        for msg in (history or []):
            role = "user" if msg.get("role") == "user" else "model"
            content = msg.get("content", "")
            if content:
                contents.append({"role": role, "parts": [{"text": content}]})
        # Add current message
        contents.append({"role": "user", "parts": [{"text": message}]})

        # 5. Call Gemini
        try:
            logger.info(
                "Gemini call: install=%s model=%s history_len=%d",
                install_id, model_name, len(contents) - 1,
            )
            response = client.models.generate_content(
                model=model_name,
                contents=contents,
            )
            return response.text
        except Exception as e:
            logger.error("Gemini API error for install %s: %s", install_id, e, exc_info=True)
            error_msg = str(e)
            if "API_KEY_INVALID" in error_msg or "PERMISSION_DENIED" in error_msg:
                return "Your Gemini API key is invalid. Please check your key in the extension settings."
            if "SAFETY" in error_msg:
                return "The response was blocked by Gemini's safety filters. Please try rephrasing your question."
            return f"Sorry, I encountered an error calling Gemini: {error_msg}"

    def on_install(self, install_id, data):
        """Store user config on install."""
        config = data.get("config", {})
        if config.get("api_key"):
            self.set_config(install_id, "api_key", config["api_key"])
        if config.get("model"):
            self.set_config(install_id, "model", config["model"])
        logger.info("Gemini extension installed: %s", install_id)

    def on_uninstall(self, install_id, data):
        """Clean up on uninstall."""
        logger.info("Gemini extension uninstalled: %s", install_id)
