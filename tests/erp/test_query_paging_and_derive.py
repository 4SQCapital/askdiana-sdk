import base64
import json
import unittest
from datetime import date, timedelta
from unittest import mock

from askdiana.erp.errors import ErpError
from askdiana.erp.mapping import map_record
from askdiana.erp.oauth import OAuth2Flow
from askdiana.erp.pack import _parse_pack, _validate
from askdiana.erp.source import fetch_raw

from tests.erp.test_credentials import raw_pack

TOKEN_YAML_AUTH = {"token": {"inputs": [{"name": "api_key", "label": "API key", "kind": "secret"}],
                             "api_base": "https://erp.example", "headers": {"Authorization": "Bearer {api_key}"},
                             "test_path": "/me"}}


def pack_with(entities: dict, paging: dict, auth: dict | None = None):
    raw = raw_pack(auth or TOKEN_YAML_AUTH)
    raw["entities"] = entities
    raw["paging"] = paging
    return _parse_pack(raw)


INVOICES = {
    "invoices": {
        "path": "/query",
        "records_path": "QueryResponse.Invoice",
        "params": {"query": "select * from Invoice STARTPOSITION {position} MAXRESULTS {size}"},
        "fields": {
            "Id": {"path": "Id", "type": "id"},
            "Total": {"path": "TotalAmt", "type": "money"},
            "Balance": {"path": "Balance", "type": "money"},
            "DueDate": {"path": "DueDate", "type": "date"},
            "Status": {"derive": [
                {"value": "Paid", "where": {"Balance": 0}},
                {"value": "Overdue", "where": {"DueDate": {"lt": "@today"}}},
                {"value": "Open"},
            ]},
        },
    },
}
QUERY_PAGING = {"page_size": 2, "max_pages": 5, "stop_on_short_page": True}


class Response:
    def __init__(self, body):
        self._body = body
        self.status_code = 200

    def json(self):
        return self._body


class TestQueryPaging(unittest.TestCase):
    def test_paging_inside_the_query_text(self):
        pack = pack_with(INVOICES, QUERY_PAGING)
        self.assertEqual(_validate(pack), [])
        rows = [{"Id": str(i)} for i in range(1, 6)]
        sent = []

        def get(path, params):
            sent.append(dict(params))
            start = int(params["query"].split("STARTPOSITION ")[1].split()[0])
            return Response({"QueryResponse": {"Invoice": rows[start - 1:start + 1]}})

        raw, truncated = fetch_raw(pack, pack.entities["invoices"], get)
        self.assertEqual(([r["Id"] for r in raw], truncated), (["1", "2", "3", "4", "5"], False))
        self.assertEqual(sent[1], {"query": "select * from Invoice STARTPOSITION 3 MAXRESULTS 2"})
        self.assertNotIn("page", sent[0])

    def test_no_page_param_and_no_placeholder_is_reported(self):
        entities = {"invoices": {**INVOICES["invoices"], "params": {"query": "select * from Invoice"}}}
        problems = _validate(pack_with(entities, QUERY_PAGING))
        self.assertTrue(any("paging has no page_param" in p for p in problems), problems)

    def test_classic_page_params_still_work(self):
        entities = {"invoices": {**INVOICES["invoices"], "params": {}}}
        pack = pack_with(entities, {**QUERY_PAGING, "page_param": "page", "size_param": "per_page"})
        sent = []
        fetch_raw(pack, pack.entities["invoices"],
                  lambda path, params: sent.append(dict(params)) or Response({"QueryResponse": {"Invoice": []}}))
        self.assertEqual(sent, [{"per_page": 2, "page": 1}])


class TestDerivedFields(unittest.TestCase):
    def setUp(self):
        self.entity = pack_with(INVOICES, QUERY_PAGING).entities["invoices"]
        self.today = date.today()

    def status(self, balance, due_in_days):
        raw = {"Id": "1", "TotalAmt": 100, "Balance": balance,
               "DueDate": (self.today + timedelta(days=due_in_days)).isoformat()}
        return map_record(self.entity, raw)["Status"]

    def test_first_matching_rule_wins(self):
        self.assertEqual(self.status(0, -10), "Paid")
        self.assertEqual(self.status(40, -1), "Overdue")
        self.assertEqual(self.status(40, 0), "Open")

    def test_derive_needs_known_fields_and_no_path(self):
        bad = {"invoices": {**INVOICES["invoices"], "fields": {
            **INVOICES["invoices"]["fields"],
            "Flag": {"path": "X", "derive": [{"value": "y"}]},
            "Late": {"derive": [{"value": "y", "where": {"Missing": 1}}]},
        }}}
        problems = _validate(pack_with(bad, QUERY_PAGING))
        self.assertTrue(any("Flag: set exactly one of path / derive" in p for p in problems), problems)
        self.assertTrue(any("unknown field 'Missing'" in p for p in problems), problems)


def jwt(claims: dict) -> str:
    def part(data):
        return base64.urlsafe_b64encode(json.dumps(data).encode()).decode().rstrip("=")
    return f"{part({'alg': 'RS256'})}.{part(claims)}.sig"


OAUTH = {"oauth2": {
    "client_id_env": "QB_ID", "client_secret_env": "QB_SECRET", "auth_server_default": "https://auth.example",
    "authorize_path": "/authorize", "token_path": "/token", "token_header": "Bearer {token}",
    "api_base_field": "qbo_api_base", "api_base_default": "https://api.example",
    "scopes": ["accounting", "openid"], "callback_params": {"realm_id": "realmId"},
    "id_token_claims": {"realm_id": "realmid"}, "api_base_suffix": "/v3/company/{realm_id}",
}}


class TestOAuthRecordValues(unittest.TestCase):
    def setUp(self):
        self.flow = OAuth2Flow(pack_with(INVOICES, QUERY_PAGING, OAUTH).auth.oauth2, "QuickBooks")
        env = mock.patch.dict("os.environ", {"QB_ID": "id", "QB_SECRET": "secret"})
        env.start()
        self.addCleanup(env.stop)

    def exchange(self, token_body: dict, extra: dict | None = None) -> dict:
        with mock.patch.object(OAuth2Flow, "_exchange_code", return_value=(token_body, "https://auth.example")):
            return self.flow.exchange("code", "https://cb", extra or {})

    def test_company_id_from_the_id_token(self):
        record = self.exchange({"access_token": "a", "id_token": jwt({"realmid": "9130"})})
        self.assertEqual(self.flow.session(record).api_base, "https://api.example/v3/company/9130")

    def test_redirect_value_wins_over_the_claim(self):
        record = self.exchange({"access_token": "a", "id_token": jwt({"realmid": "1"})}, {"realmId": "2"})
        self.assertEqual(record["realm_id"], "2")

    def test_no_company_id_is_refused(self):
        with self.assertRaises(ErpError) as ctx:
            self.exchange({"access_token": "a"})
        self.assertEqual(ctx.exception.kind, ErpError.NOT_CONNECTED)


class TestLoginUrlRule(unittest.TestCase):
    def problems(self, url: str) -> list[str]:
        auth = {"session": {
            "inputs": [{"name": "base_url", "label": "Server", "kind": "url"},
                       {"name": "client_id", "label": "Id"}, {"name": "secret", "label": "Secret", "kind": "secret"}],
            "api_base": "{base_url}/api", "headers": {"Authorization": "Bearer {session}"}, "test_path": "/me",
            "login": {"url": url, "body": {"grant_type": "client_credentials"}, "session_from": "body",
                      "session_key": "access_token"},
        }}
        return _validate(pack_with(INVOICES, QUERY_PAGING, auth))

    def test_a_url_input_may_start_the_login_url(self):
        self.assertEqual(self.problems("{base_url}/oauth2/token"), [])

    def test_other_inputs_or_schemes_may_not(self):
        self.assertTrue(any("login.url must start" in p for p in self.problems("{client_id}/token")))
        self.assertTrue(any("login.url must start" in p for p in self.problems("ftp://erp.example/token")))


class TestSegmentBars(unittest.TestCase):
    def pack(self, bars):
        raw = raw_pack(TOKEN_YAML_AUTH)
        raw["entities"] = INVOICES
        raw["paging"] = QUERY_PAGING
        raw["metrics"] = {
            "overdue": {"label": "Overdue", "entity": "invoices", "agg": "sum", "field": "Balance",
                        "where": {"Status": "Overdue"}, "format": "currency"},
            "paid": {"label": "Paid", "entity": "invoices", "agg": "sum", "field": "Total",
                     "where": {"Status": "Paid"}, "format": "currency"},
        }
        raw["dashboard"] = {"tabs": [{"id": "overview", "label": "Overview", "tiles": [], "charts": [], "bars": bars}]}
        return _parse_pack(raw)

    def test_bar_segments_are_evaluated_and_totalled(self):
        from askdiana.erp.dashboard import build_tab, entities_for_tab
        pack = self.pack([{"title": "Invoices", "segments": [
            {"metric": "overdue", "color": "#f80"}, {"metric": "paid", "label": "Paid (all time)"}]}])
        self.assertEqual(_validate(pack), [])
        tab = pack.tabs[0]
        self.assertEqual(entities_for_tab(pack, tab), ["invoices"])
        past = (date.today() - timedelta(days=5)).isoformat()
        rows = [map_record(pack.entities["invoices"], r) for r in (
            {"Id": "1", "TotalAmt": 100, "Balance": 40, "DueDate": past},
            {"Id": "2", "TotalAmt": 300, "Balance": 0, "DueDate": past})]
        bar = build_tab(pack, tab, {"invoices": rows})["bars"][0]
        self.assertEqual([(s["label"], s["amount"], s["color"]) for s in bar["segments"]],
                         [("Overdue", 40.0, "#f80"), ("Paid (all time)", 300.0, None)])
        self.assertEqual(bar["total"], "$340")

    def test_unknown_bar_metric_is_reported(self):
        problems = _validate(self.pack([{"title": "X", "segments": [{"metric": "nope"}]}]))
        self.assertTrue(any("unknown metric 'nope'" in p for p in problems), problems)


if __name__ == "__main__":
    unittest.main()
