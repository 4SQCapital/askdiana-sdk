import unittest

from askdiana.erp.dashboard import entity_index
from askdiana.erp.pack import _parse_pack
from tests.erp.test_credentials import raw_pack


class EntityIndexTest(unittest.TestCase):
    def test_lists_every_entity_with_its_fields_in_pack_order(self):
        raw = raw_pack({"token": {"inputs": [{"name": "key", "label": "Key"}], "api_base": "https://x.example",
                                "headers": {"Authorization": "{key}"}, "test_path": "/me"}})
        raw["entities"]["items"]["fields"]["Amount"] = {"path": "amount", "type": "money"}
        index = entity_index(_parse_pack(raw))
        self.assertEqual(index, [{"name": "items", "label": "Items", "fields": [
            {"name": "Id", "type": "id"}, {"name": "Amount", "type": "money"}]}])


if __name__ == "__main__":
    unittest.main()
