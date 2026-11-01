import sqlite3
from datetime import datetime
from pathlib import Path
from config import DATABASE_NAME,READING_INTERVAL_MINUTES,MAX_ROUTE_DWELL_MINUTES
BASE=Path(__file__).resolve().parent

def run(db_path=BASE/DATABASE_NAME):
    con=sqlite3.connect(db_path); c=con.cursor(); c.execute('DELETE FROM compliance_reports')
    shipments=c.execute('''SELECT s.shipment_id,s.start_time,s.end_time,p.policy_id,p.min_temperature,p.max_temperature
      FROM shipments s JOIN lots l ON l.lot_id=s.lot_id JOIN threshold_policies p ON p.product_id=l.product_id
      ORDER BY s.shipment_id''').fetchall()
    for i,(ship,start,end,policy,lo,hi) in enumerate(shipments,1):
        expected=int((datetime.fromisoformat(end)-datetime.fromisoformat(start)).total_seconds()/(READING_INTERVAL_MINUTES*60))+1
        readings=c.execute('SELECT reading_time,temperature,logger_id FROM temperature_readings WHERE shipment_id=? ORDER BY reading_time',(ship,)).fetchall()
        gaps=max(0,expected-len(readings))
        assignment=c.execute('SELECT logger_id,assigned_at,unassigned_at FROM logger_assignments WHERE shipment_id=? ORDER BY assignment_sequence LIMIT 1',(ship,)).fetchone()
        bad_logger=0
        for rt,_,logger in readings:
            if not assignment or logger!=assignment[0] or datetime.fromisoformat(rt)<datetime.fromisoformat(assignment[1]) or (assignment[2] and datetime.fromisoformat(rt)>datetime.fromisoformat(assignment[2])): bad_logger+=1
        delivery=c.execute("SELECT COUNT(*) FROM custody_events WHERE shipment_id=? AND event_type='DELIVERY'",(ship,)).fetchone()[0]
        excursion=c.execute("SELECT COUNT(*) FROM excursion_reports WHERE shipment_id=? AND decision='NON_COMPLIANT'",(ship,)).fetchone()[0]
        route_dwell=c.execute('SELECT COUNT(*) FROM route_stops WHERE shipment_id=? AND dwell_minutes>?',(ship,MAX_ROUTE_DWELL_MINUTES)).fetchone()[0]
        threshold_bad = c.execute('''
    SELECT COUNT(*)
    FROM threshold_policies p
    JOIN lots l ON l.product_id = p.product_id
    JOIN shipments s ON s.lot_id = l.lot_id
    JOIN products x ON x.product_id = l.product_id
    WHERE s.shipment_id = ?
      AND p.policy_id = ?
      AND (
          p.min_temperature <> x.min_temperature
          OR p.max_temperature <> x.max_temperature
      )
''', (ship, policy)).fetchone()[0]
        if not readings: decision='INSUFFICIENT_DATA'
        elif bad_logger or not delivery or excursion or threshold_bad or route_dwell: decision='NON_COMPLIANT'
        elif gaps: decision='INSUFFICIENT_DATA'
        else: decision='COMPLIANT'
        rationale=f'expected_readings={expected}; observed_readings={len(readings)}; gaps={gaps}; logger_assignment_violations={bad_logger}; noncompliant_excursions={excursion}; route_dwell_violations={route_dwell}; delivery_present={bool(delivery)}; threshold_mismatch={threshold_bad}'
        c.execute('INSERT INTO compliance_reports VALUES (?,?,?,?,?,?,?,?,?,?,?)',(f'COMP-{i:06d}',ship,policy,decision,len(readings),gaps,excursion,route_dwell,int(bool(delivery)),datetime.now().isoformat(timespec='seconds'),rationale))
    con.commit(); count=c.execute('SELECT COUNT(*) FROM compliance_reports').fetchone()[0]; con.close(); return count
if __name__=='__main__': print('Compliance reports generated:',run())
