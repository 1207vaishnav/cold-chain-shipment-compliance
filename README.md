# Cold-Chain Shipment Compliance Synthetic Data Project

## 1. Objective

Generate a reproducible synthetic dataset and evaluate whether temperature-sensitive shipments remained within product and route requirements.

The solution identifies temperature excursions, exposes operational exceptions, preserves shipment traceability and produces measurable compliance outcomes.

## 2. Environment and Dependencies

- Python 3.10+
- SQLite
- Python standard library
- No external Python packages required

## 3. Project Setup

Clone the repository:

```bash
git clone https://github.com/1207vaishnav/cold-chain-shipment-compliance.git
cd cold-chain-shipment-compliance
```

No package installation is required for the current implementation.

## 4. Run the Complete Dataset

Execute the complete workflow:

```bash
python main.py
```

Default configuration:

| Parameter | Value |
|---|---:|
| Shipments | 5,000 |
| Physical loggers | 1,000 |
| Temperature sampling interval | 10 minutes |
| Shipment duration | 58 hours |
| Expected baseline readings | 1,745,000 |
| Random seed | 20261022 |

The generator intentionally omits one scheduled temperature reading as a controlled missing-data anomaly. Therefore, the full dataset contains 1,744,999 actual readings.

You can also specify the configuration:

```bash
python main.py --shipments 5000 --loggers 1000 --seed 20261022 --db cold_chain.db
```

## 5. Generate a Starter Dataset

For faster testing:

```bash
python main.py --shipments 100 --loggers 25 --seed 20261022 --db starter.db
```

The same database path is passed through generation, excursion detection, compliance calculation and validation.

The generator also supports:

- `--shipments`
- `--loggers`
- `--seed`
- `--db`
- `--no-anomalies`

Use `python main.py --help` to inspect available options.

## 6. Required ID Conventions

| Entity | Example |
|---|---|
| Lot | `LOT-2026-000001` |
| Shipment | `SHP-2026-000001` |
| Physical logger | `LOG-000001` |
| Shipment-specific logger assignment | `LOG-SHP-2026-000001-01` |
| Temperature reading | `TEMP-LOG-000001-20260101080000` |
| Excursion report | `EXCR-2026-000001` |

**Logger ID interpretation:** The specification provides a shipment-specific logger naming example while requiring 1,000 logger devices for 5,000 shipments. This implementation maintains stable physical logger IDs and uses the shipment-specific naming pattern for assignment identifiers. This preserves logger reuse and shipment-level assignment traceability.

## 7. Data Model and Relationships

The implementation includes ten required core entities:

- Product
- Lot
- Shipment
- Packaging
- Logger
- TemperatureReading
- CustodyEvent
- RouteStop
- ThresholdPolicy
- ExcursionReport

Additional supporting tables:

- `logger_assignments` – connects reusable physical loggers to shipments.
- `shipment_status_history` – preserves shipment lifecycle events.
- `anomaly_issues` – records controlled anomalies and expected labels.
- `compliance_reports` – stores calculated shipment compliance outcomes.

See `schema.sql` for table definitions and `data_dictionary.md` for field-level documentation.

## 8. Data Generation and Processing Workflow

The complete pipeline follows this sequence:

1. Generate master data: products, lots, shipments, packaging and loggers.
2. Create logger assignments and generate temperature readings.
3. Record custody handoffs and route stops.
4. Store product-specific temperature thresholds and allowed excursion durations.
5. Inject controlled anomalies after baseline generation.
6. Detect temperature excursions using shipment-scoped evidence.
7. Calculate shipment compliance outcomes.
8. Validate relationships, data integrity and derived results.
9. Export the generated data and validation summary.

Historical state changes are preserved through event records instead of overwriting previous states.

## 9. Controlled Anomalies and Ground Truth

The dataset includes the following deliberate exception scenarios:

- Logger not assigned to the shipment.
- Product threshold mismatch.
- Missing scheduled temperature reading.
- Missing delivery custody event.
- Temperature excursion.
- Cross-shipment excursion aggregation guard.

Expected anomaly labels are stored separately in `ground_truth.csv`, `ground_truth.json` and the `anomaly_issues` table.

**Ground-truth separation:** These labels are evaluation data. They are not used as input features by the compliance engine to determine shipment outcomes.

The excursion detector groups evidence by shipment and policy to prevent readings from different shipments being combined into one excursion report.

## 10. Calibration Uncertainty and Route Dwell

Each logger includes calibration information, including calibration date, due date and measurement uncertainty in °C.

Raw temperature observations are retained. Since the specification does not prescribe an uncertainty decision rule, uncertainty is documented rather than used to modify measured values.

Route stops contain arrival and departure timestamps. Dwell duration is derived from these timestamps.

A maximum route dwell threshold of 120 minutes is used as a configurable synthetic assumption. This value is not presented as a regulatory requirement.

## 11. Validation

Run the validator:

```bash
python validator.py
```

The validation checks include:

- Foreign-key integrity.
- Primary-key uniqueness.
- Shipment and lot date consistency.
- Route dwell duration.
- Logger assignment date validity.
- Overlapping logger assignments.
- Reading-to-assignment relationships.
- Required delivery custody events.
- Product and threshold consistency.
- Excursion evidence and duration consistency.
- Compliance report coverage.
- Ground-truth label integrity.

Intentional, labelled anomalies are reported separately from unexpected structural failures.

### Full Dataset Validation Results

The verified full-dataset run produced:

| Validation metric | Result |
|---|---:|
| Foreign-key violations | 0 |
| Duplicate primary keys across all 14 tables | 0 |
| Invalid lot dates | 0 |
| Invalid shipment dates | 0 |
| Invalid route dwell | 0 |
| Route dwell limit violations | 0 |
| Logger assignment date errors | 0 |
| Overlapping logger assignments | 0 |
| Cross-shipment excursion evidence errors | 0 |
| Excursion duration mismatches | 0 |
| Compliance reports generated | 5,000 |
| Shipments without compliance reports | 0 |
| Ground-truth issues | 7 |
| Duplicate anomaly issue IDs | 0 |
| Invalid ground-truth decisions | 0 |

Three deliberate anomaly categories produce one expected mismatch each: logger assignment, delivery custody and product threshold. They are labelled and distinguished from unexpected failures.

**Overall structural validation: PASS.**

## 12. Tests

Run the automated test suite:

```bash
python -m pytest -v
```

The tests cover:

- Small end-to-end dataset generation.
- Excursion detection and compliance report generation.
- Baseline generation without injected anomalies.
- Structural validation.
- Preventing exports when structural validation fails.

## 13. Reproducibility

Run:

```bash
python reproducibility.py
```

The reproducibility script generates two small databases using the same seed and compares table row counts and SHA-256 checksums.

The purpose is to verify that identical configurations produce identical generated database content.

The full dataset uses seed `20261022`.

## 14. Exports

The project supports CSV, JSON and SQL exports.

Run the complete pipeline to generate all exports:

```bash
python main.py
```

Individual export commands:

```bash
python exporter.py
python sql_exporter.py
```

Generated files are stored in the `output/` directory:

- CSV exports for all database tables.
- JSON exports for all database tables.
- `cold_chain_seed.sql` for database restoration.
- `validation_summary.json` for validation results.

The SQL export was tested by restoring it into an in-memory SQLite database and checking the restored table and record counts.

## 15. Data Provenance

All generated data is synthetic.

No external shipment, customer, product or temperature data is used. `source_manifest.json` documents the synthetic data provenance.

The fixed random seed supports repeatable dataset generation.

## 16. Assumptions and Limitations

- Product names, locations, trip durations and packaging profiles are synthetic.
- Temperature thresholds and excursion allowances are configured synthetic policy values.
- Calibration uncertainty is recorded but does not modify measured temperatures.
- The 120-minute route dwell limit is a configurable assumption.
- The dataset is intended for software testing and compliance workflow evaluation.
- No real-world regulatory certification or production cold-chain validation is claimed.

## 17. Repository

GitHub: https://github.com/1207vaishnav/cold-chain-shipment-compliance

The repository contains the source code, database schema, data dictionary, synthetic ground-truth labels, tests and execution documentation.