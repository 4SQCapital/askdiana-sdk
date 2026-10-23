import time

import jwt
import pytest
from flask import Flask

from askdiana import AskDianaClient, ContextError, Persona, verify_context
from askdiana.app import ExtensionApp

KEY = "askd_test_key_for_signing_contexts_0123456789"


def _token(key=KEY, **claims):
    now = int(time.time())
    payload = {
        "iss": "askdiana",
        "aud": "inst-1",
        "sub": "u1",
        "tid": "t1",
        "ext": "e1",
        "name": "Suma",
        "email": "suma@example.test",
        "persona": {"id": "p1", "name": "AML Officer", "kind": "admin_managed"},
        "iat": now,
        "exp": now + 1800,
    }
    payload.update(claims)
    return jwt.encode(payload, key, algorithm="HS256")


def test_a_platform_token_verifies():
    ctx = verify_context(_token(), install_id="inst-1", api_key=KEY)
    assert (ctx.user_id, ctx.tenant_id, ctx.install_id, ctx.extension_id) == ("u1", "t1", "inst-1", "e1")
    assert (ctx.name, ctx.email) == ("Suma", "suma@example.test")
    assert ctx.persona == Persona(id="p1", name="AML Officer", kind="admin_managed")
    assert ctx.persona.admin_managed


def test_a_users_own_persona_is_not_admin_managed():
    persona = {"id": "p2", "name": "AML Officer", "kind": "user_managed"}
    assert not verify_context(_token(persona=persona), install_id="inst-1", api_key=KEY).persona.admin_managed


def test_the_account_view_has_no_persona():
    assert verify_context(_token(persona=None), install_id="inst-1", api_key=KEY).persona is None


@pytest.mark.parametrize(
    "token, install_id, reason",
    [
        (_token(key=KEY + "x"), "inst-1", "signature"),
        (_token(), "inst-2", "another install"),
        (_token(iss="someone"), "inst-1", "not issued"),
        (_token(exp=int(time.time()) - 120), "inst-1", "expired"),
        ("not-a-token", "inst-1", "Malformed"),
    ],
)
def test_untrusted_tokens_are_rejected(token, install_id, reason):
    with pytest.raises(ContextError, match=reason):
        verify_context(token, install_id=install_id, api_key=KEY)


def test_another_algorithm_is_rejected():
    token = jwt.encode({"iss": "askdiana", "aud": "inst-1", "exp": int(time.time()) + 60}, KEY, algorithm="HS512")
    with pytest.raises(ContextError, match="algorithm"):
        verify_context(token, install_id="inst-1", api_key=KEY)


def test_the_key_defaults_to_the_environment(monkeypatch):
    monkeypatch.setenv("ASKDIANA_API_KEY", KEY)
    assert verify_context(_token(), install_id="inst-1").user_id == "u1"


def _app():
    ext = ExtensionApp(__name__, api_key=KEY, auto_discover=False)

    @ext.flask.route("/api/whoami", methods=["GET", "POST"])
    def whoami():
        ctx = ext.request_context()
        return {"persona": ctx.persona.name if ctx and ctx.persona else None}

    @ext.flask.route("/api/officer-only", methods=["POST"])
    def officer_only():
        ctx = ext.request_context(required=True)
        return {"user": ctx.user_id}

    return ext.flask.test_client()


def test_a_view_call_carries_the_context_in_the_header():
    resp = _app().get("/api/whoami?install_id=inst-1", headers={"X-AskDiana-Context": _token()})
    assert resp.get_json() == {"persona": "AML Officer"}


def test_chat_carries_the_context_in_the_body():
    resp = _app().post("/api/whoami", json={"install_id": "inst-1", "message": "hi", "context": _token()})
    assert resp.get_json() == {"persona": "AML Officer"}


def test_no_context_is_none_on_an_older_platform():
    assert _app().get("/api/whoami?install_id=inst-1").get_json() == {"persona": None}


def test_a_forged_context_is_a_401_not_a_500():
    resp = _app().get("/api/whoami?install_id=inst-1", headers={"X-AskDiana-Context": _token(key="askd_other")})
    assert resp.status_code == 401
    assert "signature" in resp.get_json()["reason"]


def test_a_required_context_that_is_missing_is_a_401():
    assert _app().post("/api/officer-only?install_id=inst-1").status_code == 401


class _Response:
    status_code = 200

    def raise_for_status(self):
        pass

    def json(self):
        return {"success": True}


def test_with_context_sends_the_header_and_leaves_the_shared_client_alone():
    sent = []
    client = AskDianaClient(api_key=KEY, base_url="https://ask.example")
    client._session.request = lambda method, url, **kw: sent.append(kw["headers"]) or _Response()

    ctx = verify_context(_token(), install_id="inst-1", api_key=KEY)
    client.with_context(ctx).search_documents("inst-1", "closure authority")
    client.search_documents("inst-1", "closure authority")

    assert sent[0] == {"X-Install-Id": "inst-1", "X-AskDiana-Context": ctx.token}
    assert sent[1] == {"X-Install-Id": "inst-1"}


def test_with_no_context_is_the_same_client():
    client = AskDianaClient(api_key=KEY, base_url="https://ask.example")
    assert client.with_context(None) is client
