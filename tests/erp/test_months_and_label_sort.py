import unittest

from askdiana.erp.charts import pack_series
from askdiana.erp.mapping import map_record
from askdiana.erp.pack import _parse_pack, _validate

from tests.erp.test_credentials import raw_pack
from tests.erp.test_query_paging_and_derive import TOKEN_YAML_AUTH

INVOICES = {"invoices": {"path": "/invoices", "records_path": "data", "fields": {
    "Id": {"path": "id", "type": "id"},
    "Total": {"path": "total", "type": "money"},
    "Month": {"path": "date", "type": "month"},
}}}


def pack_with(chart: dict):
    raw = raw_pack(TOKEN_YAML_AUTH)
    raw["entities"] = INVOICES
    raw["charts"] = {"by_month": {"title": "Sales per Month", "entity": "invoices", "type": "bar",
                                  "group_by": "Month", "value_field": "Total", **chart}}
    return _parse_pack(raw)


class TestMonthsAndLabelSort(unittest.TestCase):
    def rows(self, pack):
        raw = [{"id": "1", "total": 10, "date": "2026-07-15"}, {"id": "2", "total": 50, "date": "2026-08-01"},
               {"id": "3", "total": 5, "date": "2026-08-30"}, {"id": "4", "total": 30, "date": "2026-09-02"}]
        return [map_record(pack.entities["invoices"], r) for r in raw]

    def test_a_month_field_cuts_the_date(self):
        pack = pack_with({"sort": "label"})
        self.assertEqual([r["Month"] for r in self.rows(pack)], ["2026-07", "2026-08", "2026-08", "2026-09"])

    def test_label_sort_keeps_months_in_order_and_top_n_keeps_the_latest(self):
        pack = pack_with({"sort": "label", "top_n": 2})
        self.assertEqual(_validate(pack), [])
        self.assertEqual(pack_series(pack.charts["by_month"], self.rows(pack)), [("2026-08", 55.0), ("2026-09", 30.0)])

    def test_value_sort_is_still_the_default(self):
        pack = pack_with({})
        self.assertEqual([label for label, _ in pack_series(pack.charts["by_month"], self.rows(pack))],
                         ["2026-08", "2026-09", "2026-07"])

    def test_numeric_strings_become_numbers(self):
        pack = pack_with({})
        row = map_record(pack.entities["invoices"], {"id": "9", "total": "120.50", "date": "2026-09-01"})
        self.assertEqual(row["Total"], 120.5)
        self.assertEqual(map_record(pack.entities["invoices"], {"id": "9", "total": "n/a"})["Total"], "n/a")

    def test_unknown_sort_is_reported(self):
        problems = _validate(pack_with({"sort": "date"}))
        self.assertTrue(any("sort must be one of" in p for p in problems), problems)


if __name__ == "__main__":
    unittest.main()
