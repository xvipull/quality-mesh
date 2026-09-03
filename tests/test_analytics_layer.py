import sqlite3
import unittest
from pathlib import Path

from quality_mesh.pipeline import run_pipeline


class AnalyticsLayerTests(unittest.TestCase):
    def test_kpi_and_reconciliation_views(self):
        root = Path(__file__).resolve().parents[1]
        run_pipeline(root)
        with sqlite3.connect(root / "data/quality_mesh.db") as connection:
            summary = connection.execute("SELECT sales_order_count, sales_revenue_usd, reconciliation_exceptions FROM vw_enterprise_kpi_summary").fetchone()
            reconciliation = connection.execute("SELECT COUNT(*) FROM vw_reconciliation_exceptions").fetchone()[0]
        self.assertEqual(summary, (4, 2550.49, 0))
        self.assertEqual(reconciliation, 0)


if __name__ == "__main__":
    unittest.main()
