import time
import unittest

from askdiana.erp.cache import TTLCache
from askdiana.erp.mapping import get_path, map_record
from askdiana.erp.pack import EntitySpec, FieldSpec

ENTITY = EntitySpec(name="contacts", label="Contacts", path="/c", records_path="data", fields={
    "Id": FieldSpec("Id", "id", type="id"),
    "Full_Name": FieldSpec("Full_Name", "Full_Name", fallback_join=("First_Name", "Last_Name")),
    "Account": FieldSpec("Account", "Account_Name.name"),
    "Score": FieldSpec("Score", "Score", type="number", default=0),
})


class TestMapping(unittest.TestCase):
    def test_get_path(self):
        self.assertEqual(get_path({"a": [{"b": 1}]}, "a.0.b"), 1)
        self.assertIsNone(get_path({"a": None}, "a.b"))
        self.assertIsNone(get_path({"a": []}, "a.3"))

    def test_map_record_lookup_fallback_default(self):
        row = map_record(ENTITY, {"id": "7", "First_Name": "Ada", "Last_Name": "Lovelace",
                        "Account_Name": {"id": "1", "name": "Acme"}})
        self.assertEqual(row, {"Id": "7", "Full_Name": "Ada Lovelace", "Account": "Acme", "Score": 0})

    def test_source_fields(self):
        self.assertEqual(ENTITY.source_fields, "Full_Name,First_Name,Last_Name,Account_Name,Score")


class TestCache(unittest.TestCase):
    def test_ttl_and_invalidate(self):
        cache = TTLCache(ttl_seconds=0)
        cache.set(("i", "deals"), [1])
        time.sleep(0.01)
        self.assertEqual(cache.get(("i", "deals")), (False, None))

        cache = TTLCache(ttl_seconds=60)
        cache.set(("i", "deals"), [1])
        cache.set(("j", "deals"), [2])
        cache.invalidate_where(lambda k: k[0] == "i")
        self.assertEqual(cache.get(("i", "deals")), (False, None))
        self.assertEqual(cache.get(("j", "deals")), (True, [2]))


if __name__ == "__main__":
    unittest.main()

