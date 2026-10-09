import unittest
from datetime import date, timedelta

from askdiana.erp.blocks import build_blocks
from askdiana.erp.pipeline import Answer
from askdiana.erp.query import apply_filters

from tests.erp.test_months_and_label_sort import pack_with

TODAY = date.today()
MONTH_START = TODAY.replace(day=1)


def rows():
    last_month = MONTH_START - timedelta(days=1)
    return [
        {"Id": "1", "Total": 100.0, "Date": MONTH_START.isoformat(), "Customer": "Acme"},
        {"Id": "2", "Total": 250.0, "Date": TODAY.isoformat(), "Customer": "Birch"},
        {"Id": "3", "Total": 999.0, "Date": last_month.isoformat(), "Customer": "Acme"},
    ]


THIS_MONTH = [{"field": "Date", "op": "gte", "value": "@month_start"}]


def answer(presentation: dict) -> Answer:
    base = {"headline": "", "summary": "", "kpis": [], "key_findings": [], "charts": [], "tables": [], "alert": None}
    return Answer({}, {"invoices": rows()}, {**base, **presentation})


class TestChatAnswers(unittest.TestCase):
    def setUp(self):
        self.pack = pack_with({})

    def test_date_tokens_work_in_filters(self):
        self.assertEqual([r["Id"] for r in apply_filters(rows(), THIS_MONTH)], ["1", "2"])

    def test_headline_states_the_filtered_total(self):
        blocks = build_blocks(self.pack, answer({"tables": [{
            "title": "Sales Invoices This Month", "endpoint": "invoices",
            "columns": ["Id", "Customer", "Total"], "filters": THIS_MONTH}]}))
        self.assertEqual(blocks[0]["content"], "$350 across 2 sales invoices this month")
        self.assertEqual(blocks[1]["content"], "2 sales invoices this month, total $350.")

    def test_no_metric_value_table_repeats_the_headline(self):
        blocks = build_blocks(self.pack, answer({
            "kpis": [{"label": "Total", "value": "$1"}],
            "tables": [{"title": "Invoices", "endpoint": "invoices", "columns": ["Id", "Total"]}]}))
        self.assertFalse(any(b["type"] == "table" and b["headers"] == ["Metric", "Value"] for b in blocks))

    def test_presenter_summary_is_kept_only_without_figures(self):
        table = [{"title": "Invoices", "endpoint": "invoices", "columns": ["Id", "Total"]}]
        kept = build_blocks(self.pack, answer({"summary": "Acme is the biggest customer.", "tables": table}))
        self.assertEqual(kept[1]["content"], "Acme is the biggest customer.")
        replaced = build_blocks(self.pack, answer({"summary": "Sales were $12,000.", "tables": table}))
        self.assertEqual(replaced[1]["content"], "3 invoices, total $1,349.")

    def test_count_only_tables_read_naturally(self):
        blocks = build_blocks(self.pack, answer({"tables": [{
            "title": "VAT Invoices", "endpoint": "invoices", "columns": ["Id", "Customer"],
            "filters": [{"field": "Id", "op": "eq", "value": "1"}]}]}))
        self.assertEqual(blocks[0]["content"], "1 VAT Invoices")
        self.assertEqual(blocks[1]["content"], "VAT invoices: 1 in total.")

    def test_chat_charts_carry_a_value_format(self):
        blocks = build_blocks(self.pack, answer({"charts": [
            {"chart_type": "bar", "title": "Sales by Customer", "endpoint": "invoices",
             "group_by": "Customer", "value_field": "Total", "agg": "sum"},
            {"chart_type": "bar", "title": "Invoices by Customer", "endpoint": "invoices",
             "group_by": "Customer", "agg": "count"}]}))
        charts = [b for b in blocks if b["type"] == "chart"]
        self.assertEqual([c["value_format"] for c in charts], ["currency_compact", "number"])


if __name__ == "__main__":
    unittest.main()
