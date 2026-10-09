import unittest
from unittest import mock

from askdiana.erp import constants as C
from askdiana.erp.dashboard import build_tab, entities_for_tab
from askdiana.erp.errors import ErpError
from askdiana.erp.mapping import map_record
from askdiana.erp.oauth import OAuth2Flow
from askdiana.erp.pack import _parse_pack, _validate
from askdiana.erp.session import Session
from askdiana.erp.source import fetch_raw

from tests.erp.test_credentials import raw_pack
from tests.erp.test_query_paging_and_derive import TOKEN_YAML_AUTH, Response, jwt

BASE = "https://api.example/v2.0/t1/production/api/v2.0/companies(c1)"
ODATA_PAGING = {"page_size": 100, "max_pages": 5, "next_link_path": "@odata.nextLink"}
CUSTOMERS = {"customers": {"path": "/customers", "records_path": "value",
                           "params": {"$select": "id,displayName"},
                           "fields": {"Id": {"path": "id", "type": "id"}}}}


def pack_with(auth=None, paging=None, extra=None):
    raw = raw_pack(auth or TOKEN_YAML_AUTH)
    raw["entities"] = CUSTOMERS
    raw["paging"] = paging or ODATA_PAGING
    raw.update(extra or {})
    return _parse_pack(raw)


class TestNextLinkPaging(unittest.TestCase):
    def test_follows_the_next_link_until_there_is_none(self):
        pack = pack_with()
        self.assertEqual(_validate(pack), [])
        pages = {
            "/customers": {"value": [{"id": "1"}, {"id": "2"}], "@odata.nextLink": f"{BASE}/customers?$skiptoken=2"},
            f"{BASE}/customers?$skiptoken=2": {"value": [{"id": "3"}]},
        }
        sent = []

        def get(path, params):
            sent.append((path, dict(params)))
            return Response(pages[path])

        raw, truncated = fetch_raw(pack, pack.entities["customers"], get)
        self.assertEqual(([r["id"] for r in raw], truncated), (["1", "2", "3"], False))
        self.assertEqual(sent[0], ("/customers", {"$select": "id,displayName"}))
        self.assertEqual(sent[1], (f"{BASE}/customers?$skiptoken=2", {}))  # the link already holds the params

    def test_stops_at_max_pages(self):
        pack = pack_with(paging={**ODATA_PAGING, "max_pages": 2})
        endless = Response({"value": [{"id": "x"}], "@odata.nextLink": f"{BASE}/customers?$skiptoken=n"})
        raw, truncated = fetch_raw(pack, pack.entities["customers"], lambda path, params: endless)
        self.assertEqual((len(raw), truncated), (2, True))

    def test_the_session_only_follows_links_under_its_api_base(self):
        session = Session(api_base=BASE)
        self.assertEqual(session.url("/customers"), f"{BASE}/customers")
        self.assertEqual(session.url(f"{BASE}/customers?$skiptoken=2"), f"{BASE}/customers?$skiptoken=2")
        for bad in ("https://evil.example/customers", f"{BASE}x/customers", "https://api.example/other"):
            with self.assertRaises(ErpError):
                session.url(bad)


OAUTH = {"oauth2": {
    "client_id_env": "BC_ID", "client_secret_env": "BC_SECRET", "auth_server_default": "https://login.example",
    "authorize_path": "/organizations/oauth2/v2.0/authorize", "token_path": "/organizations/oauth2/v2.0/token",
    "token_header": "Bearer {token}", "api_base_field": "bc_api_base", "api_base_default": "https://api.example",
    "scopes": ["https://api.example/Financials.ReadWrite.All", "offline_access", "openid"],
    "id_token_claims": {"aad_tenant": "tid"},
    "record_values": {"environment": {"env": "BC_ENVIRONMENT", "default": "production"}},
    "api_base_suffix": "/v2.0/{aad_tenant}/{environment}/api/v2.0",
    "tenant": {"path": "/companies", "id_path": "value.0.id", "label_path": "value.0.displayName",
               "path_suffix": "/companies({id})"},
}}


class FakeHttpResponse:
    ok = True
    status_code = 200

    def __init__(self, body):
        self._body = body

    def json(self):
        return self._body


class TestCompanyInThePath(unittest.TestCase):
    def setUp(self):
        self.pack = pack_with(OAUTH)
        self.flow = OAuth2Flow(self.pack.auth.oauth2, "Business Central")
        env = mock.patch.dict("os.environ", {"BC_ID": "id", "BC_SECRET": "secret"})
        env.start()
        self.addCleanup(env.stop)

    def exchange(self):
        companies = FakeHttpResponse({"value": [{"id": "c1", "displayName": "CRONUS USA, Inc."}]})
        token = {"access_token": "a", "refresh_token": "r", "id_token": jwt({"tid": "t1"})}
        with mock.patch.object(OAuth2Flow, "_exchange_code", return_value=(token, "https://login.example")), \
                mock.patch("askdiana.erp.oauth.http.request", return_value=companies) as request:
            return self.flow.exchange("code", "https://cb", {}), request

    def test_tenant_environment_and_company_build_the_address(self):
        self.assertEqual(_validate(self.pack), [])
        record, request = self.exchange()
        # The company lookup itself runs before the company is known
        self.assertEqual(request.call_args.args[1], "https://api.example/v2.0/t1/production/api/v2.0/companies")
        self.assertEqual(self.flow.session(record).api_base, BASE)
        self.assertEqual(record[C.TOKEN_ACCOUNT_LABEL], "CRONUS USA, Inc.")
        self.assertNotIn("companies", self.flow.session(record).headers)

    def test_environment_from_settings(self):
        with mock.patch.dict("os.environ", {"BC_ENVIRONMENT": "sandbox"}):
            record, _ = self.exchange()
        self.assertIn("/t1/sandbox/", self.flow.session(record).api_base)

    def test_tenant_needs_header_or_path_suffix(self):
        tenant = {k: v for k, v in OAUTH["oauth2"]["tenant"].items() if k != "path_suffix"}
        pack = pack_with({"oauth2": {**OAUTH["oauth2"], "tenant": tenant}})
        self.assertTrue(any("set exactly one of header / path_suffix" in p for p in _validate(pack)))


AGED = {"aged": {"path": "/agedAccountsReceivable", "records_path": "value", "fields": {
    "Number": "customerNumber",
    "Current": {"path": "currentAmount", "type": "money", "default": 0},
    "Period1": {"path": "period1Amount", "type": "money", "default": 0},
}}}
METRICS = {
    "current": {"label": "Not Overdue", "entity": "aged", "agg": "sum", "field": "Current",
                "where": {"Number": {"neq": ""}}, "format": "currency"},
    "period1": {"label": "0-30 Days", "entity": "aged", "agg": "sum", "field": "Period1",
                "where": {"Number": {"neq": ""}}, "format": "currency"},
}


class TestRoleCenterParts(unittest.TestCase):
    def pack(self, chart=None, tab=None):
        chart = chart or {"title": "Aged Accounts Receivable", "type": "bar", "value_format": "currency",
                          "metrics": ["current", "period1"], "colors": {"0-30 Days": "#f80"}}
        tab = tab or {"id": "home", "label": "Home", "charts": ["aged_ar"],
                      "headlines": ["{period1} is up to 30 days overdue"],
                      "tiles": [{"metric": "current", "group": "Activities"}, {"metric": "period1"}]}
        return pack_with(extra={"entities": AGED, "metrics": METRICS, "charts": {"aged_ar": chart},
                                "dashboard": {"tabs": [tab]}})

    def test_metric_chart_tile_groups_and_headlines(self):
        pack = self.pack()
        self.assertEqual(_validate(pack), [])
        tab = pack.tabs[0]
        self.assertEqual(entities_for_tab(pack, tab), ["aged"])
        rows = [map_record(pack.entities["aged"], r) for r in (
            {"customerNumber": "10000", "currentAmount": 100, "period1Amount": 50},
            {"customerNumber": "20000", "currentAmount": 10, "period1Amount": 0},
            {"customerNumber": "", "currentAmount": 110, "period1Amount": 50},  # the API's total row
        )]
        built = build_tab(pack, tab, {"aged": rows})
        self.assertEqual(built["charts"][0]["data"], [
            {"label": "Not Overdue", "value": 110.0, "color": None},
            {"label": "0-30 Days", "value": 50.0, "color": "#f80"},
        ])
        self.assertEqual([t["group"] for t in built["tiles"]], ["Activities", None])
        self.assertEqual(built["headlines"], ["$50 is up to 30 days overdue"])

    def test_metric_chart_problems_are_reported(self):
        problems = _validate(self.pack(chart={"title": "X", "type": "bar", "entity": "aged", "metrics": ["nope"]}))
        self.assertTrue(any("a metrics chart has no entity" in p for p in problems), problems)
        self.assertTrue(any("unknown metric 'nope'" in p for p in problems), problems)

    def test_unknown_headline_metric_is_reported(self):
        problems = _validate(self.pack(tab={"id": "home", "label": "Home", "tiles": [], "charts": [],
                                            "headlines": ["{missing} up"]}))
        self.assertTrue(any("headline refers to unknown metric 'missing'" in p for p in problems), problems)


class TestDateTokens(unittest.TestCase):
    def test_tokens(self):
        from datetime import date
        from askdiana.erp.mapping import date_token
        today = date(2026, 10, 2)
        self.assertEqual(date_token("@today", today), "2026-10-02")
        self.assertEqual(date_token("@today+7", today), "2026-10-09")
        self.assertEqual(date_token("@today-30", today), "2026-09-02")
        self.assertEqual(date_token("@month_start", today), "2026-10-01")
        self.assertEqual(date_token("@year_start", today), "2026-01-01")
        self.assertEqual(date_token("@tomorrow", today), "@tomorrow")
        self.assertEqual(date_token(5, today), 5)


if __name__ == "__main__":
    unittest.main()
