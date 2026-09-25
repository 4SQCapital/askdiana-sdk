import unittest
from urllib.parse import parse_qs, urlparse

import yaml
from askdiana.erp import constants as C
from askdiana.erp import http
from askdiana.erp.connect import connect_blueprint
from askdiana.erp.connector import ErpConnector
from askdiana.erp.credentials import check_url
from askdiana.erp.errors import ErpError
from askdiana.erp.pack import _parse_pack, _validate
from askdiana.erp.transport import DirectTransport
from flask import Flask, jsonify, request

from tests.erp.fakes import FakeClient, Served, env

API_KEY = "key-123"
USER, PASSWORD = "ada", "s3cret"
INSTALL_ID = "install-1"
REDIRECT_URI = "https://app.example/extensions/oauth/callback"
PUBLIC_URL = "https://ext.example"
SESSION_COOKIE = "SID"

AUTH_YAML = """
token:
  label: API key
  inputs:
    - {name: base_url, label: Server address, kind: url}
    - {name: api_key, label: API key, kind: secret}
    - {name: database, label: Database, required: false}
  api_base: "{base_url}/api"
  headers: {Authorization: "Bearer {api_key}", X-Database: "{database}"}
  test_path: /me
  account_label: "{base_url}"
basic:
  inputs:
    - {name: base_url, label: Server address, kind: url}
    - {name: username, label: Username}
    - {name: password, label: Password, kind: secret}
  api_base: "{base_url}/api"
  username: username
  password: password
  test_path: /me
  account_label: "{username}"
session:
  inputs:
    - {name: base_url, label: Server address, kind: url}
    - {name: username, label: Username}
    - {name: password, label: Password, kind: secret}
  api_base: "{base_url}/api"
  login:
    path: /Login
    body: {UserName: "{username}", Password: "{password}"}
    session_from: cookie
    session_key: SID
  cookies: {SID: "{session}"}
  test_path: /me
"""

_TEXT_KEYS = ("role", "presenter_role", "data_name", "scope_note", "out_of_scope_example", "planner_example",
            "categorical_fields_hint", "default_groupings", "presenter_examples", "fallback_headline",
            "fallback_summary", "out_of_scope_headline", "out_of_scope_summary")


def raw_pack(auth: dict) -> dict:
    assistant = {key: "x" for key in _TEXT_KEYS}
    assistant.update(intents=[], fallback_endpoints=[], fallback_charts=[], summary_metrics=[], summary_breakdowns=[])
    return {
        "id": "acme", "label": "Acme ERP", "auth": auth,
        "paging": {"page_param": "page", "size_param": "per_page", "page_size": 50, "max_pages": 2, "more_path": "more"},
        "entities": {"items": {"path": "/items", "records_path": "data", "fields": {"Id": {"path": "id", "type": "id"}}}},
        "assistant": assistant,
    }


def make_pack(auth: dict | None = None):
    pack = _parse_pack(raw_pack(auth or yaml.safe_load(AUTH_YAML)))
    assert not _validate(pack), _validate(pack)
    return pack


def mock_erp() -> Flask:
    app = Flask("mock_erp")
    state = {"sessions": set(), "logins": 0}
    app.config["STATE"] = state

    def accepted() -> bool:
        auth = request.authorization
        return (request.headers.get("Authorization") == f"Bearer {API_KEY}"
                or (auth is not None and (auth.username, auth.password) == (USER, PASSWORD))
                or request.cookies.get(SESSION_COOKIE) in state["sessions"])

    @app.post("/api/Login")
    def login():
        body = request.get_json() or {}
        if (body.get("UserName"), body.get("Password")) != (USER, PASSWORD):
            return jsonify(error="bad login"), 401
        state["logins"] += 1
        session_id = f"sid-{state['logins']}"
        state["sessions"].add(session_id)
        response = jsonify(SessionId=session_id)
        response.set_cookie(SESSION_COOKIE, session_id)
        return response

    @app.get("/api/me")
    def me():
        return (jsonify(name="Ada"), 200) if accepted() else (jsonify(error="unauthorized"), 401)

    @app.get("/api/items")
    def items():
        return (jsonify(data=[{"id": 1}], more=False), 200) if accepted() else (jsonify(error="unauthorized"), 401)

    return app


class ConnectorTestBase(unittest.TestCase):
    def setUp(self):
        self._env = env(ERP_ALLOW_INSECURE_URLS="true", EXTENSION_PUBLIC_URL=PUBLIC_URL)
        self._env.__enter__()
        self.addCleanup(self._env.__exit__, None, None, None)
        self.erp_app = mock_erp()
        self.erp = Served(self.erp_app)
        self.addCleanup(self.erp.close)
        self.pack = make_pack()
        self.connector = ErpConnector(FakeClient(), self.pack)

    def nonce(self) -> str:
        return parse_qs(urlparse(self.connector.get_auth_url(INSTALL_ID, REDIRECT_URI)).query)["nonce"][0]

    def connect(self, method: str, **form) -> str:
        return self.connector.connect_with_credentials(INSTALL_ID, self.nonce(), method,
                                                       {"base_url": self.erp.base_url, **form})


class TestCredentialLogins(ConnectorTestBase):
    def test_auth_url_opens_the_connect_page(self):
        url = urlparse(self.connector.get_auth_url(INSTALL_ID, REDIRECT_URI))
        self.assertEqual(f"{url.scheme}://{url.netloc}{url.path}", PUBLIC_URL + C.CONNECT_PAGE_PATH)
        self.assertEqual(parse_qs(url.query)["install_id"], [INSTALL_ID])

    def test_token_connects_and_blank_optional_header_is_left_out(self):
        next_url = self.connect(C.AUTH_TOKEN, api_key=API_KEY)
        self.assertEqual(next_url, f"{REDIRECT_URI}?code={C.CONNECTED_CODE}&state={INSTALL_ID}")
        status = self.connector.get_auth_status(INSTALL_ID)
        self.assertEqual((status["connected"], status["auth_method"], status["account_email"]),
                         (True, C.AUTH_TOKEN, self.erp.base_url))
        session = self.connector.session(INSTALL_ID)
        self.assertNotIn("X-Database", session.headers)
        self.assertTrue(session.get("/items").ok)

    def test_wrong_token_is_rejected_and_not_saved(self):
        with self.assertRaises(ErpError) as ctx:
            self.connect(C.AUTH_TOKEN, api_key="wrong")
        self.assertEqual(ctx.exception.kind, ErpError.UNAUTHORIZED)
        self.assertFalse(self.connector.is_connected(INSTALL_ID))

    def test_missing_required_input(self):
        with self.assertRaises(ErpError) as ctx:
            self.connect(C.AUTH_TOKEN)
        self.assertEqual(ctx.exception.kind, ErpError.INVALID)
        self.assertIn("API key", ctx.exception.message)

    def test_basic(self):
        self.connect(C.AUTH_BASIC, username=USER, password=PASSWORD)
        self.assertTrue(self.connector.session(INSTALL_ID).get("/items").ok)
        self.assertEqual(self.connector.get_auth_status(INSTALL_ID)["account_email"], USER)

    def test_session_is_reused_then_renewed_after_expiry(self):
        state = self.erp_app.config["STATE"]
        self.connect(C.AUTH_SESSION, username=USER, password=PASSWORD)
        transport = DirectTransport(self.connector, self.pack)
        self.assertTrue(transport.get(INSTALL_ID, "/items", {}).ok)
        self.assertEqual(state["logins"], 1)
        state["sessions"].clear()
        self.assertTrue(transport.get(INSTALL_ID, "/items", {}).ok)
        self.assertEqual(state["logins"], 2)

    def test_shared_http_session_never_stores_vendor_cookies(self):
        self.connect(C.AUTH_SESSION, username=USER, password=PASSWORD)
        self.assertEqual(len(http._session.cookies), 0)

    def test_connect_link_is_single_use(self):
        nonce = self.nonce()
        form = {"base_url": self.erp.base_url, "api_key": API_KEY}
        self.connector.connect_with_credentials(INSTALL_ID, nonce, C.AUTH_TOKEN, form)
        with self.assertRaises(ErpError) as ctx:
            self.connector.connect_with_credentials(INSTALL_ID, nonce, C.AUTH_TOKEN, form)
        self.assertEqual(ctx.exception.kind, ErpError.UNAUTHORIZED)

    def test_platform_callback_completes_after_the_connect_page(self):
        self.connect(C.AUTH_TOKEN, api_key=API_KEY)
        result = self.connector.handle_auth_callback(INSTALL_ID, C.CONNECTED_CODE, REDIRECT_URI)
        self.assertTrue(result["connected"])

    def test_disconnect(self):
        self.connect(C.AUTH_TOKEN, api_key=API_KEY)
        self.connector.disconnect(INSTALL_ID)
        self.assertFalse(self.connector.is_connected(INSTALL_ID))
        self.assertIsNone(self.connector.session(INSTALL_ID))


class TestConnectPage(ConnectorTestBase):
    def setUp(self):
        super().setUp()
        app = Flask("ext")
        app.register_blueprint(connect_blueprint(self.pack, self.connector))
        self.web = app.test_client()

    def test_page_renders_a_form_per_method(self):
        response = self.web.get(C.CONNECT_PAGE_PATH, query_string={"install_id": INSTALL_ID, "nonce": self.nonce()})
        html = response.get_data(as_text=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(html.count("<form"), 3)
        self.assertIn('name="api_key" type="password"', html)
        self.assertEqual(response.headers["Cache-Control"], "no-store")
        self.assertIn("frame-ancestors 'none'", response.headers["Content-Security-Policy"])

    def test_bad_link_shows_no_form(self):
        response = self.web.get(C.CONNECT_PAGE_PATH, query_string={"install_id": INSTALL_ID, "nonce": "forged"})
        self.assertEqual(response.status_code, 401)
        self.assertNotIn("<form", response.get_data(as_text=True))

    def test_error_keeps_text_but_never_echoes_secrets(self):
        nonce = self.nonce()
        response = self.web.post(C.CONNECT_API_PATH, data={
            "install_id": INSTALL_ID, "nonce": nonce, "method": C.AUTH_TOKEN,
            "base_url": self.erp.base_url, "api_key": "wrong-key-value"})
        html = response.get_data(as_text=True)
        self.assertEqual(response.status_code, 401)
        self.assertIn("rejected these details", html)
        self.assertIn(self.erp.base_url, html)
        self.assertNotIn("wrong-key-value", html)

    def test_success_redirects_to_the_platform_callback(self):
        response = self.web.post(C.CONNECT_API_PATH, data={
            "install_id": INSTALL_ID, "nonce": self.nonce(), "method": C.AUTH_TOKEN,
            "base_url": self.erp.base_url, "api_key": API_KEY})
        self.assertEqual(response.status_code, 303)
        self.assertEqual(response.headers["Location"], f"{REDIRECT_URI}?code={C.CONNECTED_CODE}&state={INSTALL_ID}")


class TestUrlCheck(unittest.TestCase):
    def test_only_public_https(self):
        with env(clear=(C.ENV_ALLOW_INSECURE_URLS,)):
            for url in ("http://8.8.8.8", "ftp://8.8.8.8", "https://127.0.0.1", "https://10.0.0.5", "https://169.254.169.254"):
                with self.assertRaises(ErpError, msg=url):
                    check_url(url)
            self.assertEqual(check_url("https://8.8.8.8"), "https://8.8.8.8")


class TestAuthValidation(unittest.TestCase):
    def problems(self, auth: dict) -> list[str]:
        return _validate(_parse_pack(raw_pack(auth)))

    def test_template_typo_is_reported(self):
        auth = yaml.safe_load(AUTH_YAML)
        auth["token"]["headers"]["Authorization"] = "Bearer {api_keey}"
        self.assertTrue(any("headers.Authorization uses unknown input '{api_keey}'" in p for p in self.problems(auth)))

    def test_basic_needs_username_and_password_inputs(self):
        auth = yaml.safe_load(AUTH_YAML)
        auth["basic"]["password"] = "pwd"
        self.assertTrue(any("'password' must name one of the inputs" in p for p in self.problems(auth)))

    def test_session_must_send_the_session(self):
        auth = yaml.safe_load(AUTH_YAML)
        auth["session"]["cookies"] = {}
        self.assertTrue(any("must use {session}" in p for p in self.problems(auth)))

    def test_unknown_method_fails_to_parse(self):
        with self.assertRaises(ErpError):
            _parse_pack(raw_pack({"magic": {}}))


if __name__ == "__main__":
    unittest.main()
