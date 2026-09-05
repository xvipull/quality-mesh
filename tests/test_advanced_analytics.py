import json
import sqlite3
import unittest
from datetime import date
from pathlib import Path

from quality_mesh.advanced_analytics import load_rules, run_advanced_analytics


class AdvancedAnalyticsTests(unittest.TestCase):
    def test_rule_config_has_unique_owned_rules(self):
        root = Path(__file__).resolve().parents[1]
        config = load_rules(root / "config/quality_rules.json")
        self.assertEqual(len(config["rules"]), 6)
        self.assertEqual(len({rule["rule_id"] for rule in config["rules"]}), 6)
        self.assertTrue(all(rule["owner"] and rule["severity"] for rule in config["rules"]))

    def test_spark_engine_publishes_governed_outputs(self):
        root = Path(__file__).resolve().parents[1]
        profiles, results, incidents = run_advanced_analytics(root, evaluation_day=date(2026, 9, 5))
        self.assertEqual(len(profiles), 16)
        self.assertTrue(all(result["status"] == "PASS" for result in results))
        self.assertEqual(incidents, [])
        with sqlite3.connect(root / "data/quality_mesh.db") as connection:
            profile_count = connection.execute("SELECT COUNT(*) FROM governed_column_profile").fetchone()[0]
            open_incidents = connection.execute("SELECT COUNT(*) FROM vw_open_data_incidents").fetchone()[0]
        self.assertEqual(profile_count, 16)
        self.assertEqual(open_incidents, 0)


if __name__ == "__main__":
    unittest.main()
