# Data Dictionary
All timestamps are synthetic ISO-8601 local timestamps (`YYYY-MM-DD HH:MM:SS`). Temperatures are °C. IDs are immutable text primary keys unless noted.

| Entity | Field(s) | Type | Required | Allowed values / units | Uniqueness and validation |
|---|---|---|---|---|---|
| Product | product_id | TEXT | Yes | PRD-NNN | Primary key |
| Product | product_name | TEXT | Yes | Synthetic name | Unique |
| Product | min_temperature, max_temperature | REAL | Yes | °C | Minimum <= maximum |
| Product | temperature_unit | TEXT | Yes | C | CHECK constraint |
| Lot | lot_id | TEXT | Yes | LOT-2026-NNNNNN | Primary key |
| Lot | product_id | TEXT | Yes | Product ID | FK to Product |
| Lot | manufacture_date, expiry_date | TEXT | Yes | ISO date | Manufacture before expiry |
| Shipment | shipment_id | TEXT | Yes | SHP-2026-NNNNNN | Primary key |
| Shipment | lot_id | TEXT | Yes | Lot ID | FK to Lot |
| Shipment | shipment_status | TEXT | Yes | PLANNED, IN_TRANSIT, DELIVERED, ON_HOLD, CANCELLED | CHECK; history records transitions |
| Shipment | origin, destination | TEXT | Yes | Synthetic location | Generator chooses different locations |
| Shipment | start_time | TEXT | Yes | Timestamp | Required |
| Shipment | end_time | TEXT | Optional | Timestamp | Must be >= start_time |
| Packaging | packaging_id | TEXT | Yes | PK text ID | Primary key |
| Packaging | shipment_id | TEXT | Yes | Shipment ID | FK; Shipment 1:N Packaging |
| Packaging | packaging_type | TEXT | Yes | INSULATED_BOX, REFRIGERATED_CONTAINER, THERMAL_BAG | CHECK |
| Packaging | insulation_profile | TEXT | Yes | STANDARD, ACTIVE_COOLING, PORTABLE | Profile label |
| Packaging | validated_min_hours | INTEGER | Yes | Hours | > 0 |
| Logger | logger_id | TEXT | Yes | LOG-NNNNNN | Physical device primary key |
| Logger | logger_status | TEXT | Yes | ACTIVE, MAINTENANCE, RETIRED | CHECK |
| Logger | calibration_date, calibration_due_date | TEXT | Yes | ISO date | Due date >= calibration date |
| Logger | calibration_uncertainty_c | REAL | Yes | °C | >= 0 |
| LoggerAssignment | assignment_id | TEXT | Yes | LOG-SHP-2026-NNNNNN-01 | Primary key; shipment-specific assignment ID |
| LoggerAssignment | logger_id, shipment_id | TEXT | Yes | Existing IDs | FKs; N:M bridge over time |
| LoggerAssignment | assignment_sequence | INTEGER | Yes | Positive integer | Unique per shipment |
| LoggerAssignment | assigned_at | TEXT | Yes | Timestamp | Required |
| LoggerAssignment | unassigned_at | TEXT | Optional | Timestamp | If present, > assigned_at |
| TemperatureReading | reading_id | TEXT | Yes | TEMP-logger-timestamp | Primary key; derived from logger ID and timestamp |
| TemperatureReading | shipment_id, logger_id | TEXT | Yes | Existing IDs | FKs; logger must be assigned at reading time |
| TemperatureReading | reading_time | TEXT | Yes | Timestamp | Unique per logger; baseline interval 10 minutes |
| TemperatureReading | temperature | REAL | Yes | °C | Evaluated against effective product policy |
| CustodyEvent | event_id | TEXT | Yes | CUST-NNNNNN-NN | Primary key |
| CustodyEvent | shipment_id | TEXT | Yes | Shipment ID | FK |
| CustodyEvent | event_time | TEXT | Yes | Timestamp | Chronological event order |
| CustodyEvent | event_type | TEXT | Yes | PICKUP, HANDOFF, DELIVERY, EXCEPTION | CHECK |
| CustodyEvent | responsible_party | TEXT | Yes | Synthetic actor | Required |
| CustodyEvent | from_party, to_party | TEXT | Optional | Synthetic actor | Captures handoff parties |
| RouteStop | stop_id | TEXT | Yes | STOP-NNNNNN-NN | Primary key |
| RouteStop | shipment_id | TEXT | Yes | Shipment ID | FK |
| RouteStop | stop_sequence | INTEGER | Yes | Positive integer | Unique per shipment |
| RouteStop | stop_location | TEXT | Yes | Synthetic location | Required |
| RouteStop | arrival_time | TEXT | Yes | Timestamp | Required |
| RouteStop | departure_time | TEXT | Optional | Timestamp | Must be >= arrival |
| RouteStop | dwell_minutes | INTEGER | Yes | Minutes | >= 0; reconciles to timestamps |
| ThresholdPolicy | policy_id | TEXT | Yes | POL-NNN | Primary key |
| ThresholdPolicy | product_id | TEXT | Yes | Product ID | FK; Product 1:N policy versions |
| ThresholdPolicy | min_temperature, max_temperature | REAL | Yes | °C | Minimum <= maximum |
| ThresholdPolicy | allowed_duration_minutes | INTEGER | Yes | Minutes | >= 0 |
| ThresholdPolicy | effective_from | TEXT | Yes | Timestamp | Required |
| ThresholdPolicy | effective_to | TEXT | Optional | Timestamp | If present, > effective_from |
| ExcursionReport | report_id | TEXT | Yes | EXCR-2026-NNNNNN | Primary key |
| ExcursionReport | shipment_id, policy_id | TEXT | Yes | Existing IDs | FKs; report belongs to one shipment/policy |
| ExcursionReport | start_time, end_time | TEXT | Yes | Timestamp | End >= start |
| ExcursionReport | excursion_duration_minutes | INTEGER | Yes | Minutes | Derived from consecutive abnormal samples plus one sampling interval |
| ExcursionReport | severity | TEXT | Yes | LOW, MEDIUM, HIGH, CRITICAL | CHECK |
| ExcursionReport | first_reading_id, last_reading_id | TEXT | Yes | Reading IDs | FKs; evidence must belong to same shipment |
| ExcursionReport | decision | TEXT | Yes | WITHIN_ALLOWANCE, NON_COMPLIANT | Compared with allowed duration |
| ShipmentStatusHistory | history_id | TEXT | Yes | SH-NNNNNN-NN | Primary key |
| ShipmentStatusHistory | shipment_id | TEXT | Yes | Shipment ID | FK; preserves status events |
| AnomalyIssue | issue_id, issue_type | TEXT | Yes | Stable issue label | Primary key; ground-truth/issue register |
| AnomalyIssue | entity_type, entity_id | TEXT | Yes | Entity reference | Identifies affected record |
| AnomalyIssue | expected_value, actual_value | TEXT | Optional | Documented values | Explains deviation |
| AnomalyIssue | expected_decision | TEXT | Yes | Decision label | Ground truth, not a feature |
| ComplianceReport | compliance_id | TEXT | Yes | COMP-NNNNNN | Primary key |
| ComplianceReport | shipment_id, policy_id | TEXT | Yes | Existing IDs | FKs; one result per shipment/policy |
| ComplianceReport | decision | TEXT | Yes | COMPLIANT, NON_COMPLIANT, INSUFFICIENT_DATA, ON_HOLD | CHECK |
| ComplianceReport | reading_count, gap_count, excursion_count, route_dwell_violation_count | INTEGER | Yes | Counts | Derived from readings, excursion reports and route stops |
| ComplianceReport | custody_complete | INTEGER | Yes | 0 or 1 | Delivery event check |
| ComplianceReport | generated_at, rationale | TEXT | Yes | Timestamp/text | Traceable explanation |

## Relationship cardinalities
- Product 1:N Lot; Lot 1:N Shipment.
- Shipment 1:N Packaging, LoggerAssignment, TemperatureReading, CustodyEvent, RouteStop, ExcursionReport, ShipmentStatusHistory and ComplianceReport.
- Logger 1:N LoggerAssignment and Logger 1:N TemperatureReading.
- Shipment N:M Logger over time through LoggerAssignment.
- Product 1:N ThresholdPolicy versions; one effective policy is expected for each product/time.
- ThresholdPolicy 1:N ExcursionReport and ComplianceReport.

Optional relationships: Shipment end_time, LoggerAssignment unassigned_at, RouteStop departure_time and ThresholdPolicy effective_to may be null. TemperatureReading requires both Shipment and Logger. All child records require valid parent IDs.
