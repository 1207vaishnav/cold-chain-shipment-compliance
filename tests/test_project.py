
import tempfile
import unittest
import sys

from pathlib import Path
from unittest.mock import patch

from data_generator import generate
from excursion_detector import detect
from compliance_engine import run
from validator import validate
from main import main as run_main


class ColdChainTests(unittest.TestCase):

    def test_small_end_to_end(self):
        with tempfile.TemporaryDirectory() as folder:
            db = Path(folder) / "test.db"

            generate(12, 3, 20261022, db, True)

            report_count = detect(db)
            compliance_count = run(db)
            result = validate(db)

            self.assertEqual(result["foreign_key_violations"], 0)
            self.assertEqual(
                result["reports_cross_shipment_evidence"], 0
            )
            self.assertEqual(result["compliance_report_count"], 12)
            self.assertEqual(result["ground_truth_issue_count"], 7)
            self.assertEqual(report_count, 2)
            self.assertEqual(compliance_count, 12)

    def test_no_anomalies_baseline(self):
        with tempfile.TemporaryDirectory() as folder:
            db = Path(folder) / "baseline.db"

            generate(4, 2, 123, db, False)

            result = validate(db)

            self.assertEqual(result["foreign_key_violations"], 0)
            self.assertEqual(
                result["readings_without_assignment_match"], 0
            )
            self.assertEqual(
                result["overlapping_logger_assignments"], 0
            )

    def test_main_stops_exports_when_validation_fails(self):

        with patch(
            "main.generate",
            return_value={"database": "failure.db"}
        ), patch(
            "main.detect",
            return_value=0
        ), patch(
            "main.compliance",
            return_value=0
        ), patch(
            "main.validate",
            return_value={"structural_checks_pass": False}
        ), patch(
            "main.export"
        ) as csv_export, patch(
            "main.export_sql"
        ) as sql_export:

            with patch.object(
                sys,
                "argv",
                [
                    "main.py",
                    "--shipments", "10",
                    "--loggers", "2",
                    "--db", "failure.db"
                ]
            ):
                with self.assertRaises(SystemExit):
                    run_main()

            csv_export.assert_not_called()
            sql_export.assert_not_called()


if __name__ == "__main__":
    unittest.main()
