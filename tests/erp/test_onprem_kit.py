import unittest
from dataclasses import replace

import yaml

from askdiana.erp import constants as C
from askdiana.erp.credentials import check_url
from askdiana.erp.errors import ErpError
from askdiana.erp.pack import _parse_pack
from askdiana.erp.source import fetch_raw
from tests.erp.fakes import env
from tests.erp.test_credentials import AUTH_YAML, raw_pack


class FakeResponse:
    def __init__(self, body: dict | None, status_code: int = 200):
        self._body, self.status_code = body, status_code

    def json(self) -> dict:
        return self._body


def pages(*batches: list[dict]):
    calls = []

    def get(path, params):
        calls.append(dict(params))
        index = params["page"] - 1
        if index >= len(batches):
            return FakeResponse(None, 204)
        return FakeResponse({"data": batches[index], "more": index + 1 < len(batches)})

    return get, calls


class TestFetchRaw(unittest.TestCase):
    def setUp(self):
        self.pack = _parse_pack(raw_pack(yaml.safe_load(AUTH_YAML)))
        self.items = self.pack.entities["items"]

    def test_reads_every_page(self):
        get, calls = pages([{"id": 1}], [{"id": 2}])
        self.assertEqual(fetch_raw(self.pack, self.items, get), ([{"id": 1}, {"id": 2}], False))
        self.assertEqual(len(calls), 2)

    def test_truncates_at_max_pages(self):
        get, _ = pages([{"id": 1}], [{"id": 2}], [{"id": 3}])
        self.assertEqual(fetch_raw(self.pack, self.items, get), ([{"id": 1}, {"id": 2}], True))
        self.assertEqual(fetch_raw(self.pack, self.items, get, max_pages=5)[1], False)

    def test_empty_status_ends_the_read(self):
        pack = replace(self.pack, paging=replace(self.pack.paging, empty_status=204))
        get, calls = pages()
        self.assertEqual(fetch_raw(pack, self.items, get), ([], False))
        self.assertEqual(len(calls), 1)


class TestPrivateNetworks(unittest.TestCase):
    def test_private_address_needs_to_be_listed(self):
        with env(clear=(C.ENV_ALLOW_INSECURE_URLS, C.ENV_PRIVATE_NETWORKS)):  # noqa: SIM117
            with self.assertRaises(ErpError):
                check_url("https://10.1.2.3")
        with env(clear=(C.ENV_ALLOW_INSECURE_URLS,), ERP_PRIVATE_NETWORKS="10.0.0.0/8, 172.16.0.0/12"):
            self.assertEqual(check_url("https://10.1.2.3"), "https://10.1.2.3")
            with self.assertRaises(ErpError):
                check_url("https://192.168.1.10")
            with self.assertRaises(ErpError):
                check_url("http://10.1.2.3")

    def test_bad_network_list_is_a_config_error(self):
        with env(clear=(C.ENV_ALLOW_INSECURE_URLS,), ERP_PRIVATE_NETWORKS="not-a-network"):  # noqa: SIM117
            with self.assertRaises(ErpError) as ctx:
                check_url("https://10.1.2.3")
        self.assertEqual(ctx.exception.kind, ErpError.CONFIG)


if __name__ == "__main__":
    unittest.main()
