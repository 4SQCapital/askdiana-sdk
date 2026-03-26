"""
Gamma Service — Gamma.app Presentation Generator for Ask DIANA

Integrates with the Gamma.app public API to generate presentations,
documents, webpages, and social posts directly from chat.
"""

import os
import json
import time
import logging

import requests
from flask import request as flask_request, jsonify

from askdiana import ChatService

logger = logging.getLogger(__name__)

GAMMA_API_BASE = "https://public-api.gamma.app/v1.0"
POLL_INTERVAL = 5 # seconds between status checks
MAX_POLL_ATTEMPTS = 24  # 24 * 5s = 2 minutes max wait

FORMAT_LABELS = {
    "presentation": "Presentation",
    "document": "Document",
    "webpage": "Webpage",
    "social": "Social Post",
}


def _rich(blocks: list) -> str:
    """Wrap blocks in the rich_response envelope."""
    return json.dumps({"type": "rich_response", "blocks": blocks})


def _error(message: str) -> str:
    """Return a rich_response with an error alert."""
    return _rich([{"type": "alert", "variant": "error", "content": message}])


class GammaChatService(ChatService):
    """Gamma — presentation generator powered by Gamma.app."""

    def respond(self, install_id, message, history=None, chat_id=None, **kwargs):
        """Generate a Gamma presentation from the user's message."""

        # 1. Get API key
        api_key = self.get_api_key(install_id)
        if not api_key:
            api_key = os.environ.get("GAMMA_API_KEY")
        if not api_key:
            return _error(
                "No Gamma API key configured. Please add your Gamma.app API key "
                "in the extension settings (Account Settings > API Keys on gamma.app). "
                "Requires a Pro, Ultra, Teams, or Business plan."
            )

        # 2. Get user preferences
        fmt = self.get_config(install_id, "format", "presentation")
        num_cards = int(self.get_config(install_id, "num_cards", 8))
        export_format = self.get_config(install_id, "export_format", "pdf")
        tone = self.get_config(install_id, "tone", "professional")
        language = self.get_config(install_id, "language", "en")

        # 3. Submit generation request
        headers = {
            "X-API-KEY": api_key,
            "Content-Type": "application/json",
        }

        payload = {
            "inputText": message,
            "textMode": "generate",
            "format": fmt,
            "numCards": num_cards,
            "exportAs": export_format,
            "textOptions": {
                "amount": "medium",
                "language": language,
            },
            "imageOptions": {
                "source": "aiGenerated",
            },
        }

        if tone:
            payload["textOptions"]["tone"] = tone

        try:
            logger.info(
                "Gamma generate: install=%s format=%s cards=%d",
                install_id, fmt, num_cards,
            )

            resp = requests.post(
                f"{GAMMA_API_BASE}/generations",
                headers=headers,
                json=payload,
                timeout=30,
            )

            if resp.status_code not in (200, 201):
                error_body = resp.text
                logger.error("Gamma API error %d: %s", resp.status_code, error_body)
                return _error(f"Gamma API error ({resp.status_code}): {error_body[:200]}")

            gen_data = resp.json()
            generation_id = gen_data.get("id") or gen_data.get("generationId")

            if not generation_id:
                return _error("Gamma API returned no generation ID. Please try again.")

            # 4. Poll for completion
            return self._poll_generation(headers, generation_id, fmt, export_format)

        except requests.Timeout:
            return _error("Gamma API request timed out. Please try again.")
        except Exception as e:
            logger.error("Gamma error for install %s: %s", install_id, e, exc_info=True)
            return _error(f"Failed to generate: {str(e)}")

    def _poll_generation(self, headers: dict, generation_id: str,
                         fmt: str, export_format: str) -> str:
        """Poll Gamma API until generation is complete or fails."""

        for attempt in range(MAX_POLL_ATTEMPTS):
            time.sleep(POLL_INTERVAL)

            try:
                resp = requests.get(
                    f"{GAMMA_API_BASE}/generations/{generation_id}",
                    headers=headers,
                    timeout=15,
                )

                if resp.status_code not in (200, 201):
                    logger.warning("Gamma poll %d: status=%d", attempt, resp.status_code)
                    continue

                data = resp.json()
                status = data.get("status", "").lower()

                if status == "completed":
                    gamma_url = data.get("gammaUrl", "")
                    export_url = data.get("exportUrl", "")
                    thumbnail_url = data.get("thumbnailUrl", "")
                    title = data.get("title", "")
                    credits_info = data.get("credits", {})

                    logger.info(
                        "Gamma generation complete: id=%s url=%s data_keys=%s",
                        generation_id, gamma_url, list(data.keys()),
                    )

                    return self._build_success_response(
                        gamma_url, export_url, fmt, export_format,
                        credits_info, thumbnail_url, title,
                    )

                elif status == "failed":
                    error = data.get("error", "Unknown error")
                    return _error(f"Gamma generation failed: {error}")

                logger.debug("Gamma poll %d: status=%s", attempt, status)

            except Exception as e:
                logger.warning("Gamma poll error attempt %d: %s", attempt, e)
                continue

        return _error(
            "Generation timed out after 2 minutes. "
            "Please check your Gamma.app dashboard."
        )

    def _build_success_response(self, gamma_url: str, export_url: str,
                                fmt: str, export_format: str,
                                credits_info: dict,
                                thumbnail_url: str = "",
                                title: str = "") -> str:
        """Build a rich_response with card + action buttons."""
        format_label = FORMAT_LABELS.get(fmt, "Presentation")
        export_label = export_format.upper()
        display_title = title or f"Gamma {format_label}"

        blocks = []

        # Thumbnail preview (if available)
        if thumbnail_url:
            blocks.append({
                "type": "image",
                "url": thumbnail_url,
                "alt": display_title,
                "caption": display_title,
                "width": "full",
            })

        # Embed via Gamma's own viewer (convert /docs/ to /embed/)
        if gamma_url:
            embed_url = gamma_url.replace("/docs/", "/embed/")
            blocks.append({
                "type": "embed",
                "url": embed_url,
                "title": display_title,
                "description": "Generated via Gamma.app",
                "aspect_ratio": "16:9",
                "allow_fullscreen": True,
            })
        elif not thumbnail_url:
            # Fallback card if no thumbnail and no PDF embed
            card = {
                "type": "card",
                "title": display_title,
                "subtitle": "Generated via Gamma.app",
                "icon": "🎨",
                "accent": "#8B5CF6",
            }
            if gamma_url:
                card["url"] = gamma_url
            blocks.append(card)

        # Action buttons
        buttons = []
        if gamma_url:
            buttons.append({
                "label": "Open in Gamma",
                "url": gamma_url,
                "style": "primary",
                "icon": "🎨",
            })
        if export_url:
            buttons.append({
                "label": f"Download {export_label}",
                "url": export_url,
                "style": "outline",
                "icon": "📥",
            })

        if buttons:
            blocks.append({"type": "buttons", "items": buttons})

        # Credits info
        if credits_info and credits_info.get("remaining") is not None:
            blocks.append({
                "type": "text",
                "content": f"Credits remaining: **{credits_info['remaining']}**",
                "style": "muted",
            })

        return _rich(blocks)

    def on_install(self, install_id, data):
        config = data.get("config", {})
        for key in ("api_key", "format", "num_cards", "export_format", "tone", "language"):
            if config.get(key):
                self.set_config(install_id, key, config[key])
        logger.info("Gamma extension installed: %s", install_id)

    def on_uninstall(self, install_id, data):
        logger.info("Gamma extension uninstalled: %s", install_id)


class GammaInvokeService:
    """Handles POST /api/invoke — post-conversation workflow invocations.

    The platform sends the full conversation context and user-selected
    parameters.  Gamma generates a presentation from the AI's last response.
    """

    def __init__(self, ext_app):
        self._app = ext_app
        self._register_route()

    def _register_route(self):
        @self._app.flask.route("/api/invoke", methods=["POST"])
        def _invoke():
            self._app.verify_request()
            body = flask_request.get_json() or {}
            return self._handle_invoke(body)

    def _handle_invoke(self, body: dict):
        install_id = body.get("install_id", "")
        params = body.get("parameters", {})
        last_response = body.get("last_response", "")
        title = body.get("title", "")
        conversation = body.get("conversation", [])

        # 1. Get API key — per-install config or env fallback
        api_key = None
        if self._app.client:
            try:
                cfg = self._app.client.get_config(install_id)
                api_key = (cfg or {}).get("api_key")
            except Exception:
                pass
        if not api_key:
            api_key = os.environ.get("GAMMA_API_KEY")
        if not api_key:
            return jsonify({
                "result_type": "rich_response",
                "data": _rich([_alert_block(
                    "No Gamma API key configured. Please add your key in extension settings."
                )]),
            }), 200

        # 2. Resolve generation parameters (user params override defaults)
        fmt = params.get("format", "presentation")
        num_cards = int(params.get("num_cards", 8))
        export_format = params.get("export_format", "pdf")

        # Build input text from conversation context
        input_text = self._build_input_text(title, last_response, conversation)

        # 3. Submit to Gamma API
        headers = {"X-API-KEY": api_key, "Content-Type": "application/json"}
        payload = {
            "inputText": input_text,
            "textMode": "generate",
            "format": fmt,
            "numCards": num_cards,
            "exportAs": export_format,
            "textOptions": {"amount": "medium", "language": "en"},
            "imageOptions": {"source": "aiGenerated"},
        }

        try:
            logger.info(
                "Gamma invoke: install=%s format=%s cards=%d",
                install_id, fmt, num_cards,
            )
            resp = requests.post(
                f"{GAMMA_API_BASE}/generations",
                headers=headers,
                json=payload,
                timeout=30,
            )

            if resp.status_code not in (200, 201):
                return jsonify({
                    "result_type": "rich_response",
                    "data": _rich([_alert_block(
                        f"Gamma API error ({resp.status_code}): {resp.text[:200]}"
                    )]),
                }), 200

            gen_data = resp.json()
            generation_id = gen_data.get("id") or gen_data.get("generationId")
            if not generation_id:
                return jsonify({
                    "result_type": "rich_response",
                    "data": _rich([_alert_block("Gamma returned no generation ID.")]),
                }), 200

            # 4. Poll for completion
            result = self._poll_generation(headers, generation_id, fmt, export_format)
            return jsonify({
                "result_type": "rich_response",
                "data": result,
            }), 200

        except requests.Timeout:
            return jsonify({
                "result_type": "rich_response",
                "data": _rich([_alert_block("Gamma API request timed out.")]),
            }), 200
        except Exception as e:
            logger.error("Gamma invoke error: %s", e, exc_info=True)
            return jsonify({
                "result_type": "rich_response",
                "data": _rich([_alert_block(f"Failed to generate: {e}")]),
            }), 200

    @staticmethod
    def _build_input_text(title: str, last_response: str, conversation: list) -> str:
        """Build the text prompt sent to Gamma from conversation context."""
        parts = []
        if title:
            parts.append(f"Title: {title}")
        if last_response:
            # Use the AI's last response as the main content
            parts.append(last_response)
        elif conversation:
            # Fallback: concatenate the last few messages
            recent = conversation[-4:]
            for msg in recent:
                role = msg.get("role", "user")
                parts.append(f"[{role}] {msg.get('content', '')}")
        return "\n\n".join(parts) if parts else "Generate a presentation"

    def _poll_generation(self, headers: dict, generation_id: str,
                         fmt: str, export_format: str) -> str:
        """Poll Gamma API until generation completes."""
        for attempt in range(MAX_POLL_ATTEMPTS):
            time.sleep(POLL_INTERVAL)
            try:
                resp = requests.get(
                    f"{GAMMA_API_BASE}/generations/{generation_id}",
                    headers=headers,
                    timeout=15,
                )
                if resp.status_code not in (200, 201):
                    continue

                data = resp.json()
                status = data.get("status", "").lower()

                if status == "completed":
                    return self._build_success_response(data, fmt, export_format)
                elif status == "failed":
                    error = data.get("error", "Unknown error")
                    return _rich([_alert_block(f"Generation failed: {error}")])

            except Exception as e:
                logger.warning("Gamma poll error attempt %d: %s", attempt, e)
                continue

        return _rich([_alert_block("Generation timed out after 2 minutes.")])

    @staticmethod
    def _build_success_response(data: dict, fmt: str, export_format: str) -> str:
        """Build rich_response JSON from Gamma's completed generation."""
        gamma_url = data.get("gammaUrl", "")
        export_url = data.get("exportUrl", "")
        thumbnail_url = data.get("thumbnailUrl", "")
        title = data.get("title", "")
        credits_info = data.get("credits", {})

        format_label = FORMAT_LABELS.get(fmt, "Presentation")
        export_label = export_format.upper()
        display_title = title or f"Gamma {format_label}"

        blocks = []

        if thumbnail_url:
            blocks.append({
                "type": "image",
                "url": thumbnail_url,
                "alt": display_title,
                "caption": display_title,
                "width": "full",
            })

        if gamma_url:
            embed_url = gamma_url.replace("/docs/", "/embed/")
            blocks.append({
                "type": "embed",
                "url": embed_url,
                "title": display_title,
                "description": "Generated via Gamma.app",
                "aspect_ratio": "16:9",
                "allow_fullscreen": True,
            })

        buttons = []
        if gamma_url:
            buttons.append({
                "label": "Open in Gamma",
                "url": gamma_url,
                "style": "primary",
            })
        if export_url:
            buttons.append({
                "label": f"Download {export_label}",
                "url": export_url,
                "style": "outline",
            })
        if buttons:
            blocks.append({"type": "buttons", "items": buttons})

        if credits_info and credits_info.get("remaining") is not None:
            blocks.append({
                "type": "text",
                "content": f"Credits remaining: **{credits_info['remaining']}**",
                "style": "muted",
            })

        return _rich(blocks)


def _alert_block(message: str) -> dict:
    """Build an error alert block."""
    return {"type": "alert", "variant": "error", "content": message}
