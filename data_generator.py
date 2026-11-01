
import argparse
import random
import sqlite3
import json

from datetime import datetime, timedelta, date
from pathlib import Path

from config import *

BASE = Path(__file__).resolve().parent
DB = BASE / DATABASE_NAME

PRODUCTS = [
    ('PRD-001', 'Vaccine A', 2, 8),
    ('PRD-002', 'Insulin B', 2, 8),
    ('PRD-003', 'Medicine C', 15, 25),
    ('PRD-004', 'Biological D', -20, -10),
    ('PRD-005', 'Vaccine E', 2, 8),
    ('PRD-006', 'Medicine F', 15, 25),
    ('PRD-007', 'Insulin G', 2, 8),
    ('PRD-008', 'Biological H', -20, -10),
    ('PRD-009', 'Vaccine I', 2, 8),
    ('PRD-010', 'Medicine J', 15, 25)
]

LOCATIONS = [
    'Hyderabad', 'Chennai', 'Bengaluru', 'Mumbai',
    'Delhi', 'Pune', 'Vijayawada', 'Nagpur'
]


def sid(i):
    return f'SHP-{YEAR}-{i:06d}'


def lid(i):
    return f'LOT-{YEAR}-{i:06d}'


def stamp(dt):
    return dt.strftime('%Y-%m-%d %H:%M:%S')


def generate(
    shipments=TOTAL_SHIPMENTS,
    loggers=TOTAL_LOGGERS,
    seed=RANDOM_SEED,
    db_path=DB,
    inject=True
):
    if shipments < 1 or loggers < 1:
        raise ValueError('Shipments and loggers must be positive')

    if inject and shipments >= 5 and loggers < 2:
        raise ValueError(
            'At least 2 loggers are required to inject a logger mismatch'
        )

    rng = random.Random(seed)
    db_path = Path(db_path)

    if db_path.exists():
        db_path.unlink()

    con = sqlite3.connect(db_path)
    con.execute('PRAGMA foreign_keys=ON')

    con.executescript((BASE / 'schema.sql').read_text())
    c = con.cursor()

    # --------------------------------------------------
    # 1. PRODUCT MASTER DATA
    # --------------------------------------------------

    c.executemany(
        'INSERT INTO products VALUES (?,?,?,?,?)',
        [
            (a, b, lo, hi, 'C')
            for a, b, lo, hi in PRODUCTS
        ]
    )

    # --------------------------------------------------
    # 2. THRESHOLD POLICIES
    # --------------------------------------------------

    c.executemany(
        'INSERT INTO threshold_policies VALUES (?,?,?,?,?,?,?)',
        [
            (
                f'POL-{i:03d}',
                p[0],
                p[2],
                p[3],
                20 if p[2] >= 0 else 15,
                '2026-01-01 00:00:00',
                None
            )
            for i, p in enumerate(PRODUCTS, 1)
        ]
    )

    # --------------------------------------------------
    # 3. PHYSICAL LOGGER MASTER DATA
    # --------------------------------------------------

    logger_rows = []

    for j in range(1, loggers + 1):
        cal = date(2025, 10, 1) + timedelta(
            days=rng.randint(0, 60)
        )

        logger_rows.append(
            (
                f'LOG-{j:06d}',
                'ACTIVE',
                cal.isoformat(),
                (cal + timedelta(days=365)).isoformat(),
                round(rng.uniform(0.1, 0.5), 2)
            )
        )

    c.executemany(
        'INSERT INTO loggers VALUES (?,?,?,?,?)',
        logger_rows
    )

    # --------------------------------------------------
    # 4. PREPARE TRANSACTION DATA
    # --------------------------------------------------

    lots = []
    ships = []
    packs = []
    assignments = []
    histories = []
    custody = []
    stops = []
    meta = {}

    base = datetime(2026, 1, 1, 8)

    for i in range(1, shipments + 1):

        # Guarantee PRD-001 exists for the threshold anomaly.
        # Other shipments use seeded random product selection.
        prod = PRODUCTS[0] if i == 1 else rng.choice(PRODUCTS)

        lot = lid(i)
        ship = sid(i)

        mfg = date(2025, 1, 1) + timedelta(
            days=rng.randint(0, 250)
        )

        expiry = mfg + timedelta(
            days=rng.randint(300, 800)
        )

        # Logger reuse in sequential four-day blocks.
        start = base + timedelta(
            days=((i - 1) // loggers) * 4,
            hours=(i % 3)
        )

        end = start + timedelta(
            hours=TRIP_DURATION_HOURS
        )

        origin = rng.choice(LOCATIONS)
        dest = rng.choice([
            x for x in LOCATIONS if x != origin
        ])

        lots.append(
            (
                lot,
                prod[0],
                mfg.isoformat(),
                expiry.isoformat()
            )
        )

        ships.append(
            (
                ship,
                lot,
                'DELIVERED',
                origin,
                dest,
                stamp(start),
                stamp(end)
            )
        )

        histories.extend([
            (
                f'SH-{i:06d}-01',
                ship,
                None,
                'PLANNED',
                stamp(start - timedelta(hours=2)),
                'planner',
                'Shipment created'
            ),
            (
                f'SH-{i:06d}-02',
                ship,
                'PLANNED',
                'IN_TRANSIT',
                stamp(start),
                'carrier',
                'Pickup confirmed'
            ),
            (
                f'SH-{i:06d}-03',
                ship,
                'IN_TRANSIT',
                'DELIVERED',
                stamp(end),
                'carrier',
                'Delivery confirmed'
            )
        ])

        ptype = rng.choice([
            'INSULATED_BOX',
            'REFRIGERATED_CONTAINER',
            'THERMAL_BAG'
        ])

        packs.append(
            (
                f'PKG-{i:06d}',
                ship,
                ptype,
                {
                    'INSULATED_BOX': 'STANDARD',
                    'REFRIGERATED_CONTAINER': 'ACTIVE_COOLING',
                    'THERMAL_BAG': 'PORTABLE'
                }[ptype],
                72
            )
        )

        logger_no = ((i - 1) % loggers) + 1
        logger = f'LOG-{logger_no:06d}'

        # Challenge-required shipment-specific assignment ID.
        assignment = f'LOG-{ship}-01'

        assignments.append(
            (
                assignment,
                logger,
                ship,
                1,
                stamp(start),
                stamp(end)
            )
        )

        meta[ship] = (prod, start, end, logger)

        custody.extend([
            (
                f'CUST-{i:06d}-01',
                ship,
                stamp(start),
                'PICKUP',
                'Supplier',
                None,
                'Carrier'
            ),
            (
                f'CUST-{i:06d}-02',
                ship,
                stamp(start + timedelta(hours=24)),
                'HANDOFF',
                'Carrier',
                'Carrier',
                'Warehouse'
            ),
            (
                f'CUST-{i:06d}-03',
                ship,
                stamp(end),
                'DELIVERY',
                'Warehouse',
                'Warehouse',
                'Receiver'
            )
        ])

        for seq, hours in (
            (1, rng.randint(8, 15)),
            (2, rng.randint(30, 42))
        ):
            arrival = start + timedelta(hours=hours)

            planned_dwell = rng.choice([
                15, 30, 45, 60, 90, 120
            ])

            departure = arrival + timedelta(
                minutes=planned_dwell
            )

            derived_dwell = int(
                (departure - arrival).total_seconds() / 60
            )

            stops.append(
                (
                    f'STOP-{i:06d}-{seq:02d}',
                    ship,
                    seq,
                    rng.choice(LOCATIONS),
                    stamp(arrival),
                    stamp(departure),
                    derived_dwell
                )
            )

    # --------------------------------------------------
    # 5. INSERT MASTER AND TRANSACTION RECORDS
    # --------------------------------------------------

    c.executemany(
        'INSERT INTO lots VALUES (?,?,?,?)',
        lots
    )

    c.executemany(
        'INSERT INTO shipments VALUES (?,?,?,?,?,?,?)',
        ships
    )

    c.executemany(
        'INSERT INTO packaging VALUES (?,?,?,?,?)',
        packs
    )

    c.executemany(
        'INSERT INTO logger_assignments VALUES (?,?,?,?,?,?)',
        assignments
    )

    c.executemany(
        'INSERT INTO shipment_status_history VALUES (?,?,?,?,?,?,?)',
        histories
    )

    c.executemany(
        'INSERT INTO custody_events VALUES (?,?,?,?,?,?,?)',
        custody
    )

    c.executemany(
        'INSERT INTO route_stops VALUES (?,?,?,?,?,?,?)',
        stops
    )

    # --------------------------------------------------
    # 6. TEMPERATURE READINGS
    # --------------------------------------------------

    key_readings = {}
    batch = []

    for i in range(1, shipments + 1):

        ship = sid(i)
        prod, start, end, logger = meta[ship]

        t = start
        idx = 0

        while t <= end:

            temp = round(
                rng.uniform(
                    prod[2] + 0.4,
                    prod[3] - 0.4
                ),
                2
            )

            if idx == 1:
                temp = float(prod[2])

            elif idx == 2:
                temp = float(prod[3])

            # Required TEMP-<logger-id>-<timestamp> format.
            rid = (
                f'TEMP-{logger}-'
                f'{t.strftime("%Y%m%d%H%M%S")}'
            )

            if i <= 5 and idx in (
                0, 100, 120, 121, 122
            ):
                key_readings[(i, idx)] = (
                    rid,
                    stamp(t)
                )

            batch.append(
                (
                    rid,
                    ship,
                    logger,
                    stamp(t),
                    temp
                )
            )

            idx += 1

            t += timedelta(
                minutes=READING_INTERVAL_MINUTES
            )

            if len(batch) >= BATCH_SIZE:
                c.executemany(
                    'INSERT INTO temperature_readings VALUES (?,?,?,?,?)',
                    batch
                )
                batch.clear()

    if batch:
        c.executemany(
            'INSERT INTO temperature_readings VALUES (?,?,?,?,?)',
            batch
        )

    # --------------------------------------------------
    # 7. INTENTIONAL ANOMALIES / GROUND TRUTH
    # --------------------------------------------------

    issues = []

    if inject and shipments >= 5:

        # Anomaly 1: Wrong logger on one reading.
        ship = sid(1)
        expected = meta[ship][3]

        expected_no = int(expected[-6:])
        wrong_no = (expected_no % loggers) + 1
        wrong = f'LOG-{wrong_no:06d}'

        rid, _ = key_readings[(1, 0)]

        c.execute(
            '''
            UPDATE temperature_readings
            SET logger_id = ?
            WHERE reading_id = ?
            ''',
            (wrong, rid)
        )

        issues.append(
            (
                'ISS-0001',
                'LOGGER_NOT_ASSIGNED_TO_SHIPMENT',
                'TemperatureReading',
                rid,
                ship,
                expected,
                wrong,
                'NON_COMPLIANT',
                'Logger on this reading is not assigned to this shipment',
                1
            )
        )

        # Anomaly 2: Threshold mismatch.
        c.execute(
            '''
            UPDATE threshold_policies
            SET max_temperature = max_temperature + 5
            WHERE policy_id = 'POL-001'
            '''
        )

        # Shipment 1 is guaranteed to use PRD-001.
        threshold_shipment = sid(1)

        issues.append(
            (
                'ISS-0002',
                'PRODUCT_THRESHOLD_MISMATCH',
                'ThresholdPolicy',
                'POL-001',
                threshold_shipment,
                '8.0',
                '13.0',
                'NON_COMPLIANT',
                'Policy maximum differs from product master maximum',
                1
            )
        )

        # Anomaly 3: Missing temperature reading.
        miss, mt = key_readings[(2, 100)]

        c.execute(
            '''
            DELETE FROM temperature_readings
            WHERE reading_id = ?
            ''',
            (miss,)
        )

        issues.append(
            (
                'ISS-0003',
                'MISSING_TEMPERATURE_READING',
                'TemperatureReading',
                miss,
                sid(2),
                mt,
                'MISSING',
                'INSUFFICIENT_DATA',
                'Scheduled ten-minute reading is absent',
                1
            )
        )

        # Anomaly 4: Missing delivery custody event.
        c.execute(
            '''
            DELETE FROM custody_events
            WHERE shipment_id = ?
              AND event_type = 'DELIVERY'
            ''',
            (sid(3),)
        )

        issues.append(
            (
                'ISS-0004',
                'CUSTODY_GAP',
                'CustodyEvent',
                'CUST-000003-03',
                sid(3),
                'DELIVERY',
                'MISSING',
                'NON_COMPLIANT',
                'Required delivery custody event is absent',
                1
            )
        )

        # Anomaly 5: Two separate temperature excursions.
        for n in (4, 5):

            prod = meta[sid(n)][0]

            for k in (120, 121, 122):

                rid, _ = key_readings[(n, k)]

                excess = (
                    9 if prod[0] == 'PRD-001' else 4
                )

                c.execute(
                    '''
                    UPDATE temperature_readings
                    SET temperature = ?
                    WHERE reading_id = ?
                    ''',
                    (prod[3] + excess, rid)
                )

            issues.append(
                (
                    f'ISS-0005-{n}',
                    'TEMPERATURE_EXCURSION',
                    'Shipment',
                    sid(n),
                    sid(n),
                    str(prod[3]),
                    str(prod[3] + excess),
                    'NON_COMPLIANT',
                    'Three consecutive readings exceed policy threshold',
                    1
                )
            )

        # Regression guard: no cross-shipment aggregation.
        issues.append(
            (
                'ISS-0006',
                'CROSS_SHIPMENT_EXCURSION_GUARD',
                'ExcursionReport',
                'REGRESSION-CASE',
                sid(4),
                'Shipment-scoped reports',
                'No cross-shipment aggregation',
                'PASS',
                'Excursion calculations must reset at shipment boundaries',
                1
            )
        )

    # --------------------------------------------------
    # 8. INSERT GROUND TRUTH
    # --------------------------------------------------

    c.executemany(
        'INSERT INTO anomaly_issues VALUES (?,?,?,?,?,?,?,?,?,?)',
        issues
    )

    con.commit()
    con.close()

    return {
        'database': str(db_path),
        'shipments': shipments,
        'loggers': loggers,
        'expected_baseline_readings': shipments * 349,
        'injected_issues': len(issues),
        'seed': seed
    }


if __name__ == '__main__':

    ap = argparse.ArgumentParser()

    ap.add_argument(
        '--shipments',
        type=int,
        default=TOTAL_SHIPMENTS
    )

    ap.add_argument(
        '--loggers',
        type=int,
        default=TOTAL_LOGGERS
    )

    ap.add_argument(
        '--seed',
        type=int,
        default=RANDOM_SEED
    )

    ap.add_argument(
        '--db',
        default=str(DB)
    )

    ap.add_argument(
        '--no-anomalies',
        action='store_true'
    )

    a = ap.parse_args()

    result = generate(
        a.shipments,
        a.loggers,
        a.seed,
        a.db,
        not a.no_anomalies
    )

    print(json.dumps(result, indent=2))
