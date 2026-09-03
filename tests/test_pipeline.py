import shutil
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

from quality_mesh.pipeline import (
    clean_orders,
    normalize_key,
    parse_amount,
    parse_date,
    run_pipeline,
)


class PipelineUnitTests(unittest.TestCase):
    def test_key_normalization_removes_separators(self):
        self.assertEqual(normalize_key(" so-1001 "), "SO1001")

    def test_date_and_amount_parsing(self):
        self.assertEqual(parse_date("31-08-2026"), "2026-08-31")
        self.assertEqual(parse_amount("1,200.00"), Decimal("1200.00"))

    def test_order_cleaning_standardizes_values(self):
        row = clean_orders([{"order_id": "so-9", "customer_id": "c-1", "order_date": "2026/09/01", "order_amount": "2.5", "currency": "usd", "category": "online"}])[0]
        self.assertEqual(row, {"order_id": "SO9", "customer_id": "C1", "order_date": "2026-09-01", "order_amount": "2.50", "currency": "USD", "category": "ONLINE"})

    def test_end_to_end_pipeline_creates_database_and_report(self):
        source_root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            shutil.copytree(source_root / "data/raw", root / "data/raw")
            (root / "data/staging").mkdir(parents=True)
            (root / "reports").mkdir()
            checks = run_pipeline(root)
            self.assertTrue(all(check["status"] == "PASS" for check in checks))
            self.assertTrue((root / "data/quality_mesh.db").exists())
            self.assertIn("15/15 checks passed", (root / "reports/data_quality_report.md").read_text())


if __name__ == "__main__":
    unittest.main()
