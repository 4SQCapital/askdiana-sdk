import os
import unittest
from pathlib import Path
from unittest import mock

from demo_data import generate

from askdiana.erp.connector import ErpConnector
from askdiana.erp.dashboard import build_tab, entities_for_tab
from askdiana.erp.pack import load_pack
from askdiana.erp.source import DataSource
from askdiana.erp.transport import DirectTransport

PACK_PATH = Path(__file__).resolve().parents[1] / "pack" / "__PACK__.yaml"


class NoStore:
    def get_data(self, install_id, namespace, key):
        return {"data": {}}


class PackTest(unittest.TestCase):
    def test_pack_loads_and_validates(self):
        pack = load_pack(str(PACK_PATH))
        self.assertTrue(pack.entities)

    def test_demo_data_fills_every_dashboard_tab(self):
        pack = load_pack(str(PACK_PATH))
        with mock.patch.dict(os.environ, {"DEMO_WHEN_DISCONNECTED": "true"}):
            connector = ErpConnector(NoStore(), pack)
            source = DataSource(pack, connector, DirectTransport(connector, pack), demo_provider=generate)
            for tab in pack.tabs:
                data, _ = source.fetch_many(None, entities_for_tab(pack, tab))
                payload = build_tab(pack, tab, data)
                self.assertEqual(len(payload["tiles"]), len(tab.tiles), tab.id)
                self.assertTrue(all(chart["data"] for chart in payload["charts"]), tab.id)


if __name__ == "__main__":
    unittest.main()
