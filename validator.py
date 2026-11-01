
import sqlite3
import json
from pathlib import Path
from config import DATABASE_NAME, OUTPUT_DIRECTORY

BASE = Path(__file__).resolve().parent

PRIMARY_KEYS = [
    ("products", "product_id"),
    ("lots", "lot_id"),
    ("shipments", "shipment_id"),
    ("packaging", "packaging_id"),
    ("loggers", "logger_id"),
    ("logger_assignments", "assignment_id"),
    ("temperature_readings", "reading_id"),
    ("custody_events", "event_id"),
    ("route_stops", "stop_id"),
    ("threshold_policies", "policy_id"),
    ("excursion_reports", "report_id"),
    ("shipment_status_history", "history_id"),
    ("anomaly_issues", "issue_id"),
    ("compliance_reports", "compliance_id"),
]


def validate(db_path=BASE / DATABASE_NAME):

    db_path = Path(db_path)
    con = sqlite3.connect(db_path)

    try:
        con.execute("PRAGMA foreign_keys=ON")
        c = con.cursor()
        r = {}

        # 1. Foreign key validation
        r["foreign_key_violations"] = len(
            c.execute("PRAGMA foreign_key_check").fetchall()
        )

        # 2. Duplicate primary key validation for all 14 tables
        for table, col in PRIMARY_KEYS:
            r[f"{table}_duplicate_primary_keys"] = c.execute(
                f"""
                SELECT COUNT(*)
                FROM (
                    SELECT {col}
                    FROM {table}
                    GROUP BY {col}
                    HAVING COUNT(*) > 1
                )
                """
            ).fetchone()[0]

        # 3. Date validation
        r["invalid_lot_dates"] = c.execute("""
            SELECT COUNT(*)
            FROM lots
            WHERE date(manufacture_date) >= date(expiry_date)
        """).fetchone()[0]

        r["invalid_shipment_dates"] = c.execute("""
            SELECT COUNT(*)
            FROM shipments
            WHERE end_time IS NOT NULL
            AND datetime(end_time) < datetime(start_time)
        """).fetchone()[0]

        # 4. Route dwell validation
        r["invalid_route_dwell"] = c.execute("""
            SELECT COUNT(*)
            FROM route_stops
            WHERE departure_time IS NOT NULL
            AND (
                datetime(departure_time) < datetime(arrival_time)
                OR dwell_minutes <>
                ROUND(
                    (julianday(departure_time)
                    - julianday(arrival_time)) * 1440
                )
            )
        """).fetchone()[0]

        r["route_dwell_limit_violations"] = c.execute("""
            SELECT COUNT(*)
            FROM route_stops
            WHERE dwell_minutes > 120
        """).fetchone()[0]

        # 5. Logger assignment validation
        r["logger_assignment_date_errors"] = c.execute("""
            SELECT COUNT(*)
            FROM logger_assignments
            WHERE unassigned_at IS NOT NULL
            AND datetime(unassigned_at) <= datetime(assigned_at)
        """).fetchone()[0]

        r["overlapping_logger_assignments"] = c.execute("""
            SELECT COUNT(*)
            FROM logger_assignments a
            JOIN logger_assignments b
            ON a.logger_id = b.logger_id
            AND a.assignment_id < b.assignment_id
            AND datetime(a.assigned_at) <
                datetime(COALESCE(b.unassigned_at, '9999-12-31'))
            AND datetime(b.assigned_at) <
                datetime(COALESCE(a.unassigned_at, '9999-12-31'))
        """).fetchone()[0]

        # 6. Reading-to-assignment validation
        c.execute("""
            CREATE INDEX IF NOT EXISTS idx_reading_assignment_check
            ON temperature_readings(
                shipment_id, logger_id, reading_time
            )
        """)

        r["readings_without_assignment_match"] = c.execute("""
            SELECT COUNT(*)
            FROM temperature_readings r
            LEFT JOIN logger_assignments a
            ON a.shipment_id = r.shipment_id
            AND a.logger_id = r.logger_id
            AND datetime(r.reading_time) >= datetime(a.assigned_at)
            AND datetime(r.reading_time) <=
                datetime(COALESCE(a.unassigned_at, '9999-12-31'))
            WHERE a.assignment_id IS NULL
        """).fetchone()[0]

        # 7. Custody validation
        r["shipments_missing_delivery"] = c.execute("""
            SELECT COUNT(*)
            FROM shipments s
            WHERE NOT EXISTS (
                SELECT 1
                FROM custody_events e
                WHERE e.shipment_id = s.shipment_id
                AND e.event_type = 'DELIVERY'
            )
        """).fetchone()[0]

        # 8. Product threshold validation
        r["threshold_product_mismatches"] = c.execute("""
            SELECT COUNT(*)
            FROM threshold_policies p
            JOIN products x
            ON x.product_id = p.product_id
            WHERE p.min_temperature <> x.min_temperature
            OR p.max_temperature <> x.max_temperature
        """).fetchone()[0]

        # 9. Excursion evidence validation
        r["reports_cross_shipment_evidence"] = c.execute("""
            SELECT COUNT(*)
            FROM excursion_reports e
            JOIN temperature_readings a
            ON a.reading_id = e.first_reading_id
            JOIN temperature_readings b
            ON b.reading_id = e.last_reading_id
            WHERE a.shipment_id <> e.shipment_id
            OR b.shipment_id <> e.shipment_id
        """).fetchone()[0]

        r["excursion_duration_mismatch"] = c.execute("""
            SELECT COUNT(*)
            FROM excursion_reports
            WHERE excursion_duration_minutes <>
            (
                ROUND(
                    (julianday(end_time) - julianday(start_time)) * 1440
                ) + 10
            )
        """).fetchone()[0]

        # 10. Compliance report validation
        r["compliance_report_count"] = c.execute("""
            SELECT COUNT(*)
            FROM compliance_reports
        """).fetchone()[0]

        r["shipments_without_compliance_report"] = c.execute("""
            SELECT COUNT(*)
            FROM shipments s
            WHERE NOT EXISTS (
                SELECT 1
                FROM compliance_reports cr
                WHERE cr.shipment_id = s.shipment_id
            )
        """).fetchone()[0]

        # 11. Labelled anomaly validation
        r["labelled_logger_mismatch_count"] = c.execute("""
            SELECT COUNT(*)
            FROM anomaly_issues
            WHERE issue_type = 'LOGGER_NOT_ASSIGNED_TO_SHIPMENT'
        """).fetchone()[0]

        r["labelled_custody_gap_count"] = c.execute("""
            SELECT COUNT(*)
            FROM anomaly_issues
            WHERE issue_type = 'CUSTODY_GAP'
        """).fetchone()[0]

        r["labelled_threshold_mismatch_count"] = c.execute("""
            SELECT COUNT(*)
            FROM anomaly_issues
            WHERE issue_type = 'PRODUCT_THRESHOLD_MISMATCH'
        """).fetchone()[0]

        r["unlabelled_logger_mismatches"] = max(
            0,
            r["readings_without_assignment_match"]
            - r["labelled_logger_mismatch_count"]
        )

        r["unlabelled_custody_gaps"] = max(
            0,
            r["shipments_missing_delivery"]
            - r["labelled_custody_gap_count"]
        )

        r["unlabelled_threshold_mismatches"] = max(
            0,
            r["threshold_product_mismatches"]
            - r["labelled_threshold_mismatch_count"]
        )

        r["ground_truth_issue_count"] = c.execute("""
            SELECT COUNT(*)
            FROM anomaly_issues
        """).fetchone()[0]

        r["duplicate_anomaly_issue_ids"] = c.execute("""
            SELECT COUNT(*)
            FROM (
                SELECT issue_id
                FROM anomaly_issues
                GROUP BY issue_id
                HAVING COUNT(*) > 1
            )
        """).fetchone()[0]

        r["invalid_ground_truth_decisions"] = c.execute("""
            SELECT COUNT(*)
            FROM anomaly_issues
            WHERE expected_decision NOT IN (
                'COMPLIANT',
                'NON_COMPLIANT',
                'INSUFFICIENT_DATA',
                'ON_HOLD',
                'PASS'
            )
        """).fetchone()[0]

        # 12. Structural validation result
        intentional_issue_keys = {
            "readings_without_assignment_match",
            "shipments_missing_delivery",
            "threshold_product_mismatches",
            "labelled_logger_mismatch_count",
            "labelled_custody_gap_count",
            "labelled_threshold_mismatch_count",
        }

        informational_keys = {
            "compliance_report_count",
            "ground_truth_issue_count",
        }

        r["structural_checks_pass"] = all(
            value == 0
            for key, value in r.items()
            if key not in intentional_issue_keys
            and key not in informational_keys
        )

        # 13. Save validation summary
        output_dir = BASE / OUTPUT_DIRECTORY
        output_dir.mkdir(parents=True, exist_ok=True)

        summary_path = output_dir / "validation_summary.json"

        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(r, f, indent=2)

        r["validation_summary_file"] = str(summary_path)

        return r

    finally:
        con.close()


if __name__ == "__main__":
    print(json.dumps(validate(), indent=2))
