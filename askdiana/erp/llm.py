from __future__ import annotations

import json
import re
from typing import Any, Protocol

from . import constants as C
from . import http
from .errors import ErpError
from .settings import env_str

_FENCE = re.compile(r"^```(?:json)?\s*(.*?)\s*```$", re.DOTALL)
_FIRST_OBJECT = re.compile(r"\{.*\}", re.DOTALL)


class LLMClient(Protocol):
    def complete_json(self, system_prompt: str, user_message: str) -> dict: ...


def extract_json(text: str) -> dict:
    text = text.strip()
    fence = _FENCE.match(text)
    if fence:
        text = fence.group(1)
    if not text.startswith("{"):
        match = _FIRST_OBJECT.search(text)
        if match:
            text = match.group(0)
    return json.loads(text)


class _HttpClient:
    def __init__(self, url: str, api_key: str, model: str) -> None:
        self._url, self._key, self._model = url, api_key, model

    def _post(self, headers: dict[str, str], body: dict[str, Any]) -> dict:
        response = http.request("POST", self._url, timeout=C.LLM_TIMEOUT_SECONDS,
                            headers={"Content-Type": "application/json", **headers}, json=body)
        response.raise_for_status()
        return response.json()


class OpenAICompatibleClient(_HttpClient):
    def complete_json(self, system_prompt: str, user_message: str) -> dict:
        headers = {"Authorization": f"Bearer {self._key}"} if self._key else {}
        data = self._post(headers, {
            "model": self._model,
            "messages": [{"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message}],
            "temperature": C.LLM_TEMPERATURE,
        })
        return extract_json(data["choices"][0]["message"]["content"])


class AnthropicClient(_HttpClient):
    def complete_json(self, system_prompt: str, user_message: str) -> dict:
        data = self._post({"x-api-key": self._key, "anthropic-version": C.ANTHROPIC_API_VERSION}, {
            "model": self._model,
            "max_tokens": C.LLM_MAX_TOKENS,
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_message}],
        })
        text = "".join(block.get("text", "") for block in data["content"] if block.get("type") == "text")
        return extract_json(text)


class _NotConfigured:
    def __init__(self, message: str) -> None:
        self._message = message

    def complete_json(self, system_prompt: str, user_message: str) -> dict:
        raise ErpError(ErpError.CONFIG, self._message)


_PROVIDERS = {
    C.PROVIDER_OPENAI: OpenAICompatibleClient,
    C.PROVIDER_ANTHROPIC: AnthropicClient,
}


def _env(name: str) -> str:
    return env_str(name) or env_str(C.LEGACY_LLM_ENV.get(name, ""))


def llm_from_env() -> LLMClient:
    provider = env_str(C.ENV_LLM_PROVIDER, C.DEFAULT_LLM_PROVIDER).lower()
    client_cls = _PROVIDERS.get(provider)
    if client_cls is None:
        return _NotConfigured(f"{C.ENV_LLM_PROVIDER}={provider!r} must be one of {sorted(_PROVIDERS)}")
    missing = [name for name in (C.ENV_LLM_URL, C.ENV_LLM_MODEL) if not _env(name)]
    if provider == C.PROVIDER_ANTHROPIC and not _env(C.ENV_LLM_API_KEY):
        missing.append(C.ENV_LLM_API_KEY)
    if missing:
        return _NotConfigured(f"LLM not configured: set {', '.join(missing)}")
    return client_cls(_env(C.ENV_LLM_URL), _env(C.ENV_LLM_API_KEY), _env(C.ENV_LLM_MODEL))
