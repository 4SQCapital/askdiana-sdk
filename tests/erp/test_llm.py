import unittest

from askdiana.erp import constants as C
from askdiana.erp.errors import ErpError
from askdiana.erp.llm import AnthropicClient, OpenAICompatibleClient, llm_from_env
from flask import Flask, jsonify, request

from tests.erp.fakes import Served, env

ALL_LLM_ENV = (C.ENV_LLM_PROVIDER, C.ENV_LLM_URL, C.ENV_LLM_API_KEY, C.ENV_LLM_MODEL, *C.LEGACY_LLM_ENV.values())


def mock_llm() -> Flask:
    app = Flask("mock_llm")
    app.config["SEEN"] = []

    @app.post("/v1/chat/completions")
    def chat_completions():
        app.config["SEEN"].append((dict(request.headers), request.get_json()))
        return jsonify(choices=[{"message": {"content": '```json\n{"answer": "openai"}\n```'}}])

    @app.post("/v1/messages")
    def messages():
        app.config["SEEN"].append((dict(request.headers), request.get_json()))
        return jsonify(content=[{"type": "text", "text": 'Here you go: {"answer": "anthropic"}'}])

    return app


class TestLlmFromEnv(unittest.TestCase):
    def test_openai_compatible_is_the_default(self):
        with env(clear=ALL_LLM_ENV, LLM_URL="https://llm.example/v1/chat/completions", LLM_MODEL="m"):
            self.assertIsInstance(llm_from_env(), OpenAICompatibleClient)

    def test_legacy_genius2_names_still_work(self):
        with env(clear=ALL_LLM_ENV, GENIUS2_URL="https://genius2.example/v1/chat/completions",
                GENIUS2_API_KEY="k", GENIUS2_MODEL="genius2"):
            self.assertIsInstance(llm_from_env(), OpenAICompatibleClient)

    def test_anthropic(self):
        with env(clear=ALL_LLM_ENV, LLM_PROVIDER="anthropic", LLM_URL="https://api.example/v1/messages",
                LLM_API_KEY="k", LLM_MODEL="m"):
            self.assertIsInstance(llm_from_env(), AnthropicClient)

    def test_missing_config_fails_only_when_used(self):
        for extra in ({}, {"LLM_PROVIDER": "anthropic", "LLM_URL": "u", "LLM_MODEL": "m"}, {"LLM_PROVIDER": "nope"}):
            with env(clear=ALL_LLM_ENV, **extra):
                client = llm_from_env()                          # the extension still starts
                with self.assertRaises(ErpError) as ctx:
                    client.complete_json("system", "question")
                self.assertEqual(ctx.exception.kind, ErpError.CONFIG)


class TestRequestFormats(unittest.TestCase):
    def setUp(self):
        self.app = mock_llm()
        self.server = Served(self.app)
        self.addCleanup(self.server.close)

    def test_openai_compatible(self):
        client = OpenAICompatibleClient(self.server.base_url + "/v1/chat/completions", "key", "genius2")
        self.assertEqual(client.complete_json("be brief", "hi"), {"answer": "openai"})
        headers, body = self.app.config["SEEN"][-1]
        self.assertEqual(headers["Authorization"], "Bearer key")
        self.assertEqual([m["role"] for m in body["messages"]], ["system", "user"])
        self.assertEqual(body["model"], "genius2")

    def test_openai_compatible_without_key_sends_no_auth_header(self):
        OpenAICompatibleClient(self.server.base_url + "/v1/chat/completions", "", "local").complete_json("s", "u")
        headers, _ = self.app.config["SEEN"][-1]
        self.assertNotIn("Authorization", headers)

    def test_anthropic(self):
        client = AnthropicClient(self.server.base_url + "/v1/messages", "key", "claude-model")
        self.assertEqual(client.complete_json("be brief", "hi"), {"answer": "anthropic"})
        headers, body = self.app.config["SEEN"][-1]
        self.assertEqual((headers["X-Api-Key"], headers["Anthropic-Version"]), ("key", C.ANTHROPIC_API_VERSION))
        self.assertEqual(body["system"], "be brief")
        self.assertEqual(body["messages"], [{"role": "user", "content": "hi"}])
        self.assertEqual(body["max_tokens"], C.LLM_MAX_TOKENS)


if __name__ == "__main__":
    unittest.main()
