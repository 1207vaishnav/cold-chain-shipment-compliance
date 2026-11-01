# Cold-Chain Shipment Compliance Synthetic Data Project

## Objective
Generate a reproducible synthetic dataset and evaluate whether temperature-sensitive shipments remained within product and route requirements. The solution exposes exceptions, preserves traceability and produces measurable compliance outcomes.

## Environment and dependencies
Python 3.10+; Python standard library only. SQLite is used for persistence. No external package installation is required.

## Run the complete default dataset
From this folder:
```bash
python main.py
```
Default scale: 5,000 shipments, 1,000 physical loggers, 10-minute sampling, 349 expected readings per 58-hour shipment. Seed: `20261022`.

## Starter dataset
The same generator supports a smaller scale:
```bash
python data_generator.py --shipments 100 --loggers 25 --db starter.db
```
Then run the detectors with the same DB path through Python or set `DATABASE_NAME` in config for the standard workflow. The generator accepts `--shipments`, `--loggers`, `--seed`, `--db`, and `--no-anomalies`.

## Required ID conventions
- Lot: `LOT-2026-000001`
- Shipment: `SHP-2026-000001`
- Physical logger: `LOG-000001`
- Shipment-specific logger assignment: `LOG-SHP-2026-000001-01`
- Reading: `TEMP-LOG-000001-20260101080000`
- Excursion report: `EXCR-2026-000001`

The prompt gives a shipment-specific logger naming example while requiring 1,000 logger devices for 5,000 shipments. This implementation keeps 1,000 stable physical logger IDs and uses the shipment-specific pattern for the assignment identifier. This is a documented modelling interpretation to satisfy both instructions.

## Data model
Ten required core entities are implemented, plus `logger_assignments` as the N:M bridge, `shipment_status_history` for lifecycle event history, `anomaly_issues` for labelled controlled exceptions, and `compliance_reports` for outcomes. See `schema.sql` and `data_dictionary.md`.

## Workflow
1. Create master data (Product, Lot, Shipment, Packaging, Logger).
2. Create valid assignments, readings, custody events and route stops.
3. Store policy limits, allowed excursion durations and effective dates.
4. Inject labelled deviations only after the baseline has been generated.
5. Calculate shipment-scoped excursion reports and compliance outcomes from evidence.
6. Validate and export CSV, JSON and SQL.

## Required edge cases
- Logger not assigned to shipment.
- Product threshold mismatch.
- Missing scheduled temperature reading.
- Missing delivery custody event.
- Cross-shipment excursion aggregation guard. The detector groups by shipment and policy, and each report references first/last evidence readings.

`anomaly_issues` and `ground_truth.json` hold expected labels separately; the compliance engine does not use those labels as input features.

## Calibration uncertainty and route dwell
Each logger includes calibration date, due date and uncertainty in °C. Raw temperature observations are retained. The problem statement does not specify an uncertainty decision rule, so uncertainty is documented rather than used to alter measured values. Route stops include variable dwell durations, derived from arrival/departure timestamps. For this synthetic example, a maximum dwell threshold of 120 minutes is configured; the problem statement does not prescribe a numerical route dwell limit, so this is an explicit configurable assumption.

## Validation and reproducibility
```bash
python excursion_detector.py
python compliance_engine.py
python validator.py
python -m unittest discover -s tests -v
python reproducibility.py
```
The reproducibility script regenerates two small databases with the same seed and compares row counts and SHA-256 table checksums.

## Exports
`exporter.py` exports all database tables to CSV and JSON under `output/`. `sql_exporter.py` creates a SQL seed dump. `source_manifest.json` records synthetic provenance; no external data is used.

## Synthetic assumptions and limitations
Product names, locations, trip duration, packaging profiles, excursion allowances and calibration uncertainty ranges are synthetic assumptions because the specification does not prescribe exact values. No real-world regulatory certification is claimed. External data is not required or used.
