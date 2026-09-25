import unittest

from askdiana.erp import constants as C
from askdiana.erp.query import (
    aggregate,
    apply_filters,
    build_table,
    format_value,
    group_values,
    order_groups,
    rank_rows,
)

ROWS = [
    {"Stage": "Qualification", "Amount": 100, "Owner": "A", "Name": "x"},
    {"Stage": "Closed Won", "Amount": 300, "Owner": "B", "Name": "y"},
    {"Stage": "Closed Lost", "Amount": 50, "Owner": "A", "Name": "z"},
    {"Stage": "Custom Stage", "Amount": 500, "Owner": "B", "Name": "w"},
    {"Stage": None, "Amount": "n/a", "Owner": "C", "Name": "v"},
]


class TestFilters(unittest.TestCase):
    def test_not_in(self):
        rows = apply_filters(ROWS, [{"field": "Stage", "op": "not_in", "value": ["Closed Won", "Closed Lost"]}])
        self.assertEqual([r["Name"] for r in rows], ["x", "w"])

    def test_contains_is_case_insensitive(self):
        self.assertEqual(len(apply_filters(ROWS, [{"field": "Stage", "op": "contains", "value": "closed"}])), 2)

    def test_type_mismatch_and_unknown_op_drop_rows(self):
        self.assertEqual(apply_filters(ROWS, [{"field": "Name", "op": "gt", "value": 1}]), [])
        self.assertEqual(apply_filters(ROWS, [{"field": "Amount", "op": "between", "value": 1}]), [])


class TestAggregation(unittest.TestCase):
    def test_aggregate(self):
        self.assertEqual(aggregate(ROWS, agg=C.AGG_SUM, field="Amount"), 950)
        self.assertEqual(aggregate(ROWS, agg=C.AGG_COUNT), 5)
        self.assertEqual(aggregate(ROWS, agg=C.AGG_COUNT_DISTINCT, field="Owner"), 3)

    def test_group_values_skips_missing_keys(self):
        self.assertEqual(group_values(ROWS, group_by="Owner", value_field="Amount"),
                         {"A": 150.0, "B": 800.0, "C": 0.0})

    def test_non_numeric_value_field_returns_none(self):
        self.assertIsNone(group_values(ROWS, group_by="Owner", value_field="Name"))

    def test_fixed_order_keeps_unknown_groups(self):
        grouped = group_values(ROWS, group_by="Stage", value_field="Amount")
        ordered = order_groups(grouped, order=["Qualification", "Closed Won", "Closed Lost"])
        self.assertEqual([k for k, _ in ordered], ["Qualification", "Closed Won", "Closed Lost", "Custom Stage"])

    def test_rank_rows(self):
        self.assertEqual(rank_rows(ROWS, label_field="Name", value_field="Amount", top_n=2),
                         [("w", 500.0), ("y", 300.0)])


class TestFormatting(unittest.TestCase):
    def test_formats(self):
        self.assertEqual(format_value(620_000, C.FMT_CURRENCY_COMPACT, symbol="$", decimals=0), "$620K")
        self.assertEqual(format_value(1_250_000, C.FMT_CURRENCY_COMPACT, symbol="$", decimals=0), "$1.2M")
        self.assertEqual(format_value(50, C.FMT_PERCENT, symbol="$", decimals=0), "50%")
        self.assertEqual(format_value(1234, C.FMT_NUMBER, symbol="$", decimals=0), "1,234")
        self.assertEqual(format_value(None, C.FMT_NUMBER, symbol="$", decimals=0), "—")

    def test_build_table_drops_unknown_columns_and_formats_money(self):
        table = build_table(ROWS[:2], entity="deals", title="Deals", columns=["Name", "Amount", "Nope"],
                            field_type=lambda c: C.FIELD_MONEY if c == "Amount" else C.FIELD_STRING,
                            symbol="$", decimals=0, sort_by="Amount", sort_desc=True)
        self.assertEqual(table.headers, ["Name", "Amount"])
        self.assertEqual(table.display_rows[0], ["y", "$300"])
        self.assertEqual(table.all_rows[0], ["y", 300])


if __name__ == "__main__":
    unittest.main()
