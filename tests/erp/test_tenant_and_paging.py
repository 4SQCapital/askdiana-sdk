import base64
import json
import unittest
from dataclasses import replace

from flask import Flask, jsonify, request

from askdiana.erp import constants as C
from askdiana.erp.connector import ErpConnector
from askdiana.erp.credentials import CredentialFlow
from askdiana.erp.errors import ErpError
from askdiana.erp.pack import _parse_pack, _validate
from askdiana.erp.source import fetch_raw
from tests.erp.fakes import FakeClient, Served, env
from tests.erp.test_credentials import raw_pack

INSTALL_ID = "install-1"
REDIRECT_URI = "https://app.example/extensions/oauth/callback"
CLIENT_ID, CLIENT_SECRET = "cid", "csecret"
TENANTS = [
    {"id": "c-1", "authEventId": "event-old", "tenantId": "org-old", "tenantName": "Old Org"},
    {"id": "c-2", "authEventId": "event-new", "tenantId": "org-new", "tenantName": "New Org"},
]


def fake_jwt(claims: dict) -> str:
    def part(data: dict) -> str:
        return base64.urlsafe_b64encode(json.dumps(data).encode()).decode().rstrip("=")
    return f"{part({'alg': 'none'})}.{part(claims)}.sig"


def mock_vendor(*, tenants=TENANTS) -> Flask:
    app = Flask("mock_vendor")
    state = {"revoked": [], "logins": 0, "tokens": set()}
    app.config["STATE"] = state

    def issue(event: str = "event-new") -> dict:
        token = fake_jwt({"authentication_event_id": event, "n": len(state["tokens"])})
        state["tokens"].add(token)
        return {"access_token": token, "refresh_token": f"r-{len(state['tokens'])}", "expires_in": 1800}

    def bearer_ok() -> bool:
        return request.headers.get("Authorization", "").removeprefix("Bearer ") in state["tokens"]

    @app.post("/connect/token")
    def token():
        grant = request.form.get("grant_type")
        if grant == "client_credentials":
            auth = request.authorization
            if auth is None or (auth.username, auth.password) != (CLIENT_ID, CLIENT_SECRET):
                return jsonify(error="invalid_client"), 400
            state["logins"] += 1
            return jsonify(issue())
        if request.form.get("client_id") != CLIENT_ID:
            return jsonify(error="invalid_client"), 400
        return jsonify(issue())

    @app.post("/connect/revocation")
    def revoke():
        state["revoked"].append(dict(request.form))
        return "", 200

    @app.get("/connections")
    def connections():
        if not bearer_ok():
            return "", 401
        event = request.args.get("authEventId")
        return jsonify([t for t in tenants if not event or t["authEventId"] == event])

    @app.get("/api/items")
    def items():
        if not bearer_ok():
            return "", 401
        if request.headers.get("Accept") != "application/json":
            return "<xml/>", 200
        if request.headers.get("xero-tenant-id", "org-new") != "org-new":
            return jsonify(error="wrong tenant"), 403
        rows = [{"id": i, "kind": request.args.get("where")} for i in range(5)]
        page, size = int(request.args["page"]), int(request.args["pageSize"])
        return jsonify({"Items": rows[(page - 1) * size: page * size]})

    return app


def oauth_auth(base_url: str) -> dict:
    return {"oauth2": {
        "client_id_env": "V_CLIENT_ID", "client_secret_env": "V_CLIENT_SECRET",
        "auth_server_default": base_url, "token_path": "/connect/token",
        "revoke_path": "/connect/revocation", "revoke_client_auth": True,
        "authorize_server_default": "https://login.vendor.example/", "authorize_path": "/identity/connect/authorize",
        "token_header": "Bearer {token}", "api_base_field": "api_base", "api_base_default": base_url,
        "scopes": ["offline_access", "items.read"],
        "headers": {"Accept": "application/json"},
        "tenant": {"path": "/connections", "id_path": "0.tenantId", "label_path": "0.tenantName",
                "header": "xero-tenant-id", "auth_event_claim": "authentication_event_id",
                "auth_event_param": "authEventId"},
    }}


def client_credentials_auth(base_url: str) -> dict:
    return {"session": {
        "label": "Custom connection",
        "inputs": [{"name": "client_id", "label": "Client id"},
                {"name": "client_secret", "label": "Client secret", "kind": "secret"}],
        "api_base": base_url,
        "login": {"url": f"{base_url}/connect/token", "encoding": "form",
                "basic_auth": ["client_id", "client_secret"],
                "body": {"grant_type": "client_credentials", "scope": "items.read"},
                "session_from": "body", "session_key": "access_token", "ttl_seconds": 1500},
        "headers": {"Authorization": "Bearer {session}", "Accept": "application/json"},
        "test_path": "/api/items?page=1&pageSize=1",
        "account_label": "Custom connection {client_id}",
    }}


def build(raw: dict):
    pack = _parse_pack(raw)
    problems = _validate(pack)
    assert not problems, problems
    return pack


def xero_like(base_url: str, auth: dict) -> dict:
    raw = raw_pack(auth)
    raw["paging"] = {"page_param": "page", "size_param": "pageSize", "page_size": 2, "max_pages": 10,
                    "stop_on_short_page": True}
    raw["entities"]["items"] = {"path": "/api/items", "records_path": "Items",
                                "params": {"where": 'Type=="ACCREC"'},
                                "fields": {"Id": {"path": "id", "type": "id"}, "Kind": "kind"}}
    return raw


class TenantDiscoveryTest(unittest.TestCase):
    def setUp(self):
        self.app = mock_vendor()
        self.served = Served(self.app)
        self.addCleanup(self.served.close)
        self._env = env(V_CLIENT_ID=CLIENT_ID, V_CLIENT_SECRET=CLIENT_SECRET)
        self._env.__enter__()
        self.addCleanup(self._env.__exit__, None, None, None)
        self.pack = build(xero_like(self.served.base_url, oauth_auth(self.served.base_url)))
        self.connector = ErpConnector(FakeClient(), self.pack)

    def test_sign_in_stores_the_organisation_of_this_sign_in(self):
        result = self.connector.handle_auth_callback(INSTALL_ID, "code", REDIRECT_URI)
        record = self.connector.get_tokens(INSTALL_ID)
        self.assertEqual((record[C.TOKEN_TENANT_ID], result["account_email"]), ("org-new", "New Org"))

    def test_sign_in_page_is_on_the_login_host(self):
        url = self.connector.oauth.auth_url(INSTALL_ID, REDIRECT_URI)
        self.assertTrue(url.startswith("https://login.vendor.example/identity/connect/authorize?"), url)
        with env(V_LOGIN_URL=self.served.base_url):
            flow = ErpConnector(FakeClient(), replace(self.pack, auth=replace(self.pack.auth, oauth2=replace(
                self.pack.auth.oauth2, authorize_server_env="V_LOGIN_URL")))).oauth
            self.assertTrue(flow.auth_url(INSTALL_ID, REDIRECT_URI).startswith(self.served.base_url + "/identity/"))

    def test_every_call_sends_the_tenant_and_accept_headers(self):
        self.connector.handle_auth_callback(INSTALL_ID, "code", REDIRECT_URI)
        headers = self.connector.session(INSTALL_ID).headers
        self.assertEqual(headers["xero-tenant-id"], "org-new")
        self.assertEqual(headers["Accept"], "application/json")

    def test_refresh_keeps_the_organisation(self):
        self.connector.handle_auth_callback(INSTALL_ID, "code", REDIRECT_URI)
        session = self.connector.session(INSTALL_ID, force_refresh=True)
        self.assertEqual(session.headers["xero-tenant-id"], "org-new")

    def test_no_organisation_means_not_connected(self):
        app = mock_vendor(tenants=[])
        served = Served(app)
        self.addCleanup(served.close)
        pack = build(xero_like(served.base_url, oauth_auth(served.base_url)))
        with self.assertRaises(ErpError) as ctx:
            ErpConnector(FakeClient(), pack).handle_auth_callback(INSTALL_ID, "code", REDIRECT_URI)
        self.assertEqual(ctx.exception.kind, ErpError.NOT_CONNECTED)

    def test_disconnect_revokes_with_client_credentials(self):
        self.connector.handle_auth_callback(INSTALL_ID, "code", REDIRECT_URI)
        self.connector.disconnect(INSTALL_ID)
        revoked = self.app.config["STATE"]["revoked"][0]
        self.assertEqual((revoked["client_id"], revoked["client_secret"]), (CLIENT_ID, CLIENT_SECRET))

    def test_fixed_params_and_short_page_paging(self):
        self.connector.handle_auth_callback(INSTALL_ID, "code", REDIRECT_URI)
        session = self.connector.session(INSTALL_ID)
        calls = []

        def get(path, params):
            calls.append(dict(params))
            return session.get(path, params)

        rows, truncated = fetch_raw(self.pack, self.pack.entities["items"], get)
        self.assertEqual((len(rows), truncated, len(calls)), (5, False, 3))
        self.assertTrue(all(row["kind"] == 'Type=="ACCREC"' for row in rows))


class ClientCredentialsLoginTest(unittest.TestCase):
    def setUp(self):
        self.app = mock_vendor()
        self.served = Served(self.app)
        self.addCleanup(self.served.close)
        pack = build(xero_like(self.served.base_url, client_credentials_auth(self.served.base_url)))
        self.flow = CredentialFlow(pack.auth.credentials["session"], "Vendor")

    def test_form_login_with_basic_auth_gets_a_bearer_token(self):
        values = {"client_id": CLIENT_ID, "client_secret": CLIENT_SECRET}
        self.flow.verify(INSTALL_ID, values)
        self.flow.session(INSTALL_ID, values)
        self.assertEqual(self.app.config["STATE"]["logins"], 1)

    def test_wrong_secret_is_rejected(self):
        with self.assertRaises(ErpError) as ctx:
            self.flow.verify(INSTALL_ID, {"client_id": CLIENT_ID, "client_secret": "nope"})
        self.assertEqual(ctx.exception.kind, ErpError.UNAUTHORIZED)


class ValidationTest(unittest.TestCase):
    def test_paging_needs_a_stop_rule(self):
        raw = xero_like("https://v.example", oauth_auth("https://v.example"))
        raw["paging"].pop("stop_on_short_page")
        self.assertTrue(any("stop_on_short_page" in p for p in _validate(_parse_pack(raw))))

    def test_login_needs_exactly_one_of_path_or_url(self):
        auth = client_credentials_auth("https://v.example")
        auth["session"]["login"]["path"] = "/token"
        problems = _validate(_parse_pack(raw_pack(auth)))
        self.assertTrue(any("exactly one of path" in p for p in problems))

    def test_basic_auth_must_name_inputs(self):
        auth = client_credentials_auth("https://v.example")
        auth["session"]["login"]["basic_auth"] = ["client_id", "nope"]
        problems = _validate(_parse_pack(raw_pack(auth)))
        self.assertTrue(any("basic_auth" in p for p in problems))


if __name__ == "__main__":
    unittest.main()
