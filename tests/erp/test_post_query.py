import unittest
from datetime import date, timedelta
from unittest import mock

from askdiana.erp.pack import _validate
from askdiana.erp.session import Session
from askdiana.erp.source import fetch_raw

from tests.erp.test_query_paging_and_derive import pack_with

INVOICES = {
    "invoices": {
        "path": "/services/core/query",
        "method": "post",
        "records_path": "ia::result",
        "body": {
            "object": "accounts-receivable/invoice",
            "filters": [{"$ge": {"invoiceDate": "@today-30"}}],
            "start": "{position}",
            "size": "{size}",
        },
        "fields": {
            "Id": {"path": "key", "type": "id"},
            "Customer": "customer.name",
            "Total": {"path": "totalTxnAmount", "type": "money"},
        },
    },
}
PAGING = {"page_size": 2, "max_pages": 5, "more_path": "ia::meta.next", "fields_body": "fields"}


class FakeResponse:
    status_code = 200

    def __init__(self, body):
        self._body = body

    def json(self):
        return self._body


class TestPostQuery(unittest.TestCase):
    def test_pages_through_a_post_query(self):
        pack = pack_with(INVOICES, PAGING)
        self.assertEqual(_validate(pack), [])
        rows = [{"key": str(i), "customer": {"name": f"C{i}"}, "totalTxnAmount": "10"} for i in range(1, 6)]
        sent = []

        def post(path, params, body=None):
            sent.append((path, body))
            start = body["start"]
            page = rows[start - 1:start - 1 + body["size"]]
            more = start + body["size"] if start - 1 + body["size"] < len(rows) else None
            return FakeResponse({"ia::result": page, "ia::meta": {"start": start, "next": more}})

        raw, truncated = fetch_raw(pack, pack.entities["invoices"], post)
        self.assertFalse(truncated)
        self.assertEqual([r["key"] for r in raw], ["1", "2", "3", "4", "5"])
        self.assertEqual([body["start"] for _, body in sent], [1, 3, 5])
        first = sent[0][1]
        self.assertEqual(first["size"], 2)  # a bare "{size}" is sent as a number
        self.assertEqual(first["fields"], ["key", "customer.name", "totalTxnAmount"])
        self.assertEqual(first["filters"], [{"$ge": {"invoiceDate": (date.today() - timedelta(days=30)).isoformat()}}])
        self.assertEqual(first["object"], "accounts-receivable/invoice")
        self.assertEqual(sent[0][0], "/services/core/query")

    def test_get_entities_are_unchanged(self):
        pack = pack_with({"items": {"path": "/items", "records_path": "data",
                                    "fields": {"Id": {"path": "id", "type": "id"}}}},
                         {"page_param": "page", "page_size": 2, "max_pages": 1, "more_path": "more"})
        calls = []
        fetch_raw(pack, pack.entities["items"], lambda path, params: calls.append(params) or FakeResponse({"data": []}))
        self.assertEqual(calls, [{"page": 1}])

    def test_validation(self):
        no_body = {"invoices": {**INVOICES["invoices"], "body": {}}}
        self.assertTrue(any("needs a body" in p for p in _validate(pack_with(no_body, PAGING))))
        get_with_body = {"invoices": {**INVOICES["invoices"], "method": "get"}}
        self.assertTrue(any("body needs method: POST" in p for p in _validate(pack_with(get_with_body, PAGING))))
        unpaged = {"invoices": {**INVOICES["invoices"], "body": {"object": "x"}}}
        self.assertTrue(any("page_param" in p for p in _validate(pack_with(unpaged, PAGING))))
        bad_method = {"invoices": {**INVOICES["invoices"], "method": "put"}}
        self.assertTrue(any("method must be one of" in p for p in _validate(pack_with(bad_method, PAGING))))

    def test_session_sends_the_body_as_json(self):
        session = Session(api_base="https://api.example/ia/api/v1", headers={"Authorization": "Bearer t"})
        with mock.patch("askdiana.erp.session.http.request") as request:
            session.send("POST", "/services/core/query", {}, {"object": "x"})
        method, url = request.call_args.args
        self.assertEqual((method, url), ("POST", "https://api.example/ia/api/v1/services/core/query"))
        self.assertEqual(request.call_args.kwargs["json"], {"object": "x"})
        with mock.patch("askdiana.erp.session.http.request") as request:
            session.get("/items")
        self.assertNotIn("json", request.call_args.kwargs)


if __name__ == "__main__":
    unittest.main()
