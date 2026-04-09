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
POLL_INTERVAL = 5  # seconds between status checks
MAX_POLL_ATTEMPTS = 24  # 24 * 5s = 2 minutes max wait

FORMAT_LABELS = {
    "presentation": "Presentation",
    "document": "Document",
    "webpage": "Webpage",
    "social": "Social Post",
}
VALID_FORMATS = set(FORMAT_LABELS.keys())
VALID_EXPORT_FORMATS = {"pdf", "pptx", "png"}
VALID_LANGUAGES = {"en", "ar", "fr", "es", "de", "zh", "ja", "ko"}
VALID_CONTENT_AMOUNTS = {"brief", "medium", "detailed"}
VALID_TEMPLATE_MODES = {"none", "manual", "auto_select"}


def _rich(blocks: list) -> str:
    """Wrap blocks in the rich_response envelope."""
    return json.dumps({"type": "rich_response", "blocks": blocks})


def _error(message: str) -> str:
    """Return a rich_response with an error alert."""
    return _rich([{"type": "alert", "variant": "error", "content": message}])


def _safe_int(value, default: int) -> int:
    try:
        return int(value)
    except Exception:
        return default


def _normalize_options(raw: dict, defaults: dict) -> dict:
    """Normalize and validate generation options with safe fallbacks."""
    opts = {
        "format": (raw.get("format") or defaults.get("format") or "presentation").lower(),
        "num_cards": _safe_int(raw.get("num_cards") or defaults.get("num_cards") or 8, 8),
        "export_format": (raw.get("export_format") or defaults.get("export_format") or "pdf").lower(),
        "tone": (raw.get("tone") if raw.get("tone") is not None else defaults.get("tone", "professional")),
        "language": (raw.get("language") or defaults.get("language") or "en").lower(),
        "template_mode": (raw.get("template_mode") or defaults.get("template_mode") or "none").lower(),
        "template_id": (raw.get("template_id") or defaults.get("template_id") or "").strip(),
        "content_amount": (raw.get("content_amount") or defaults.get("content_amount") or "medium").lower(),
        "logo_url": (raw.get("logo_url") or defaults.get("logo_url") or "").strip(),
        "brand_name": (raw.get("brand_name") or defaults.get("brand_name") or "").strip(),
    }

    if opts["format"] not in VALID_FORMATS:
        opts["format"] = "presentation"
    if opts["export_format"] not in VALID_EXPORT_FORMATS:
        opts["export_format"] = "pdf"
    if opts["language"] not in VALID_LANGUAGES:
        opts["language"] = "en"
    if opts["content_amount"] not in VALID_CONTENT_AMOUNTS:
        opts["content_amount"] = "medium"
    if opts["template_mode"] not in VALID_TEMPLATE_MODES:
        opts["template_mode"] = "none"
    if opts["num_cards"] < 1:
        opts["num_cards"] = 1
    if opts["num_cards"] > 25:
        opts["num_cards"] = 25

    return opts


def _fetch_templates(headers: dict) -> list:
    """Try known template endpoints and normalize the response."""
    candidates = ("/templates", "/design-templates", "/user/templates")
    for path in candidates:
        try:
            resp = requests.get(f"{GAMMA_API_BASE}{path}", headers=headers, timeout=15)
            if resp.status_code not in (200, 201):
                continue
            body = resp.json()
            items = body.get("templates") or body.get("items") or body.get("data") or []
            results = []
            for item in items:
                template_id = str(item.get("id") or item.get("templateId") or "").strip()
                name = str(item.get("name") or item.get("title") or template_id).strip()
                if template_id:
                    results.append({"id": template_id, "name": name})
            if results:
                return results
        except Exception as e:
            logger.debug("Template fetch failed at %s: %s", path, e)
    return []


def _resolve_template(headers: dict, options: dict) -> dict:
    """Resolve template selection with precedence and fallback."""
    manual_id = options.get("template_id", "")
    mode = options.get("template_mode", "none")
    preferred_name = options.get("template_name", "").lower()

    if manual_id:
        return {"id": manual_id, "name": options.get("template_name") or manual_id, "source": "manual"}
    if mode != "auto_select":
        return {}

    templates = _fetch_templates(headers)
    if not templates:
        return {}

    if preferred_name:
        for t in templates:
            if preferred_name in t["name"].lower():
                return {"id": t["id"], "name": t["name"], "source": "auto_select"}

    first = templates[0]
    return {"id": first["id"], "name": first["name"], "source": "auto_select"}


def _build_input_text(base_text: str, options: dict) -> str:
    """Append optional branding instructions only when explicitly set."""
    additions = []
    if options.get("brand_name"):
        additions.append(f"Use brand name '{options['brand_name']}' in the output.")
    if options.get("logo_url"):
        additions.append(f"If supported, apply this logo: {options['logo_url']}")


    if not additions:
        return base_text
    return base_text + "\n\n" + "\n".join(additions)


def _build_generation_payload(input_text: str, options: dict, template: dict) -> dict:
    payload = {
        "inputText": input_text,
        "textMode": "generate",
        "format": options["format"],
        "numCards": options["num_cards"],
        "exportAs": options["export_format"],
        "textOptions": {
            "amount": options["content_amount"],
            "language": options["language"],
        },
        "imageOptions": {"source": "aiGenerated"},
    }

    if options.get("tone"):
        payload["textOptions"]["tone"] = options["tone"]
    if template.get("id"):
        payload["themeId"] = template["id"]

    return payload


def _build_success_response(data: dict, fmt: str, export_format: str, context: dict = None) -> str:
    import re as _re

    gamma_url = data.get("gammaUrl", "") or data.get("url", "")
    export_url = data.get("exportUrl", "") or data.get("downloadUrl", "")
    thumbnail_url = data.get("thumbnailUrl", "") or data.get("imageUrl", "")
    title = data.get("title", "")
    format_label = FORMAT_LABELS.get(fmt, "Presentation")
    export_label = export_format.upper()
    display_title = title or f"Gamma {format_label}"

    # Derive embed URL: gamma.app/docs/<id> → gamma.app/embed/<id>
    embed_url = ""
    if gamma_url:
        match = _re.search(r"gamma\.app/(?:docs|embed)/([^/?#]+)", gamma_url)
        if match:
            embed_url = f"https://gamma.app/embed/{match.group(1)}"

    blocks = []

    if embed_url:
        blocks.append({
            "type": "embed",
            "url": embed_url,
            "title": display_title,
            "description": f"Your {format_label} is ready",
            "aspect_ratio": "16:9",
            "allow_fullscreen": True,
        })
    elif thumbnail_url:
        blocks.append({
            "type": "image",
            "url": thumbnail_url,
            "alt": display_title,
            "caption": display_title,
            "width": "full",
        })
    else:
        card_body = f"Your {format_label} is ready."
        if context and context.get("template_name"):
            card_body += f" Theme: **{context['template_name']}**"
        blocks.append({
            "type": "card",
            "title": display_title,
            "body": card_body,
            "icon": "🎨",
            "url": gamma_url or None,
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

    if not blocks:
        blocks.append({
            "type": "text",
            "content": f"Your {format_label} has been generated successfully.",
        })

    return _rich(blocks)


def _run_generation(headers: dict, payload: dict, options: dict, response_context: dict) -> str:
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

    for attempt in range(MAX_POLL_ATTEMPTS):
        time.sleep(POLL_INTERVAL)
        try:
            poll_resp = requests.get(
                f"{GAMMA_API_BASE}/generations/{generation_id}",
                headers=headers,
                timeout=15,
            )
            if poll_resp.status_code not in (200, 201):
                logger.warning("Gamma poll %d: status=%d", attempt, poll_resp.status_code)
                continue

            data = poll_resp.json()
            status = data.get("status", "").lower()
            if status == "completed":
                logger.info("Gamma generation complete: id=%s", generation_id)
                return _build_success_response(
                    data,
                    options["format"],
                    options["export_format"],
                    response_context,
                )
            if status == "failed":
                error = data.get("error", "Unknown error")
                return _error(f"Gamma generation failed: {error}")
        except Exception as e:
            logger.warning("Gamma poll error attempt %d: %s", attempt, e)
            continue

    return _error(
        "Generation timed out after 2 minutes. "
        "Please check your Gamma.app dashboard."
    )


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

        # 2. Resolve options
        defaults = {
            "format": self.get_config(install_id, "format", "presentation"),
            "num_cards": self.get_config(install_id, "num_cards", 8),
            "export_format": self.get_config(install_id, "export_format", "pdf"),
            "tone": self.get_config(install_id, "tone", "professional"),
            "language": self.get_config(install_id, "language", "en"),
            "template_mode": self.get_config(install_id, "template_mode", "none"),
            "template_id": self.get_config(install_id, "template_id", ""),
            "content_amount": self.get_config(install_id, "content_amount", "medium"),
            "logo_url": self.get_config(install_id, "logo_url", ""),
            "brand_name": self.get_config(install_id, "brand_name", ""),
        }
        options = _normalize_options({}, defaults)

        # 3. Build payload with optional template + advanced controls
        headers = {
            "X-API-KEY": api_key,
            "Content-Type": "application/json",
        }
        template = _resolve_template(headers, options)
        input_text = _build_input_text(message, options)
        payload = _build_generation_payload(input_text, options, template)
        response_context = {
            "template_id": template.get("id", ""),
            "template_name": template.get("name", ""),
        }

        try:
            logger.info(
                "Gamma generate: install=%s format=%s cards=%d template_mode=%s template=%s",
                install_id,
                options["format"],
                options["num_cards"],
                options["template_mode"],
                template.get("id", ""),
            )
            return _run_generation(headers, payload, options, response_context)

        except requests.Timeout:
            return _error("Gamma API request timed out. Please try again.")
        except Exception as e:
            logger.error("Gamma error for install %s: %s", install_id, e, exc_info=True)
            return _error(f"Failed to generate: {str(e)}")

    def on_install(self, install_id, data):
        config = data.get("config", {})
        for key in (
            "api_key",
            "format",
            "num_cards",
            "export_format",
            "tone",
            "language",
            "template_mode",
            "template_id",
            "content_amount",
            "logo_url",
            "brand_name",
        ):
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
        defaults = {
            "format": "presentation",
            "num_cards": 8,
            "export_format": "pdf",
            "tone": "professional",
            "language": "en",
            "template_mode": "none",
            "template_id": "",
            "content_amount": "medium",
            "logo_url": "",
            "brand_name": "",
        }
        if self._app.client:
            try:
                cfg = self._app.client.get_config(install_id) or {}
                defaults.update(cfg)
            except Exception:
                pass
        options = _normalize_options(params, defaults)

        # Build input text from conversation context
        input_text = self._build_input_text(title, last_response, conversation)
        input_text = _build_input_text(input_text, options)

        # 3. Submit to Gamma API
        headers = {"X-API-KEY": api_key, "Content-Type": "application/json"}
        template = _resolve_template(headers, options)
        payload = _build_generation_payload(input_text, options, template)
        response_context = {
            "template_id": template.get("id", ""),
            "template_name": template.get("name", ""),
        }

        try:
            logger.info(
                "Gamma invoke: install=%s format=%s cards=%d template_mode=%s template=%s model=%s",
                install_id,
                options["format"],
                options["num_cards"],
                options["template_mode"],
                template.get("id", ""),
                options.get("model", ""),
            )
            result = _run_generation(headers, payload, options, response_context)
            # _run_generation returns a JSON string; parse it so the stored result
            # is a proper dict and survives round-trips through the DB cleanly.
            try:
                result_dict = json.loads(result)
            except Exception:
                result_dict = {"type": "rich_response", "blocks": []}
            return jsonify({
                "result_type": "rich_response",
                "data": result_dict,
            }), 200

        except requests.Timeout:
            return jsonify({
                "result_type": "rich_response",
                "data": {"type": "rich_response", "blocks": [_alert_block("Gamma API request timed out.")]},
            }), 200
        except Exception as e:
            logger.error("Gamma invoke error: %s", e, exc_info=True)
            return jsonify({
                "result_type": "rich_response",
                "data": {"type": "rich_response", "blocks": [_alert_block(f"Failed to generate: {e}")]},
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

def _alert_block(message: str) -> dict:
    """Build an error alert block."""
    return {"type": "alert", "variant": "error", "content": message}
