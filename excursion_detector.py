import sqlite3
from datetime import datetime
from pathlib import Path
from config import DATABASE_NAME
BASE=Path(__file__).resolve().parent

def detect(db_path=BASE/DATABASE_NAME):
    con=sqlite3.connect(db_path); c=con.cursor(); c.execute('DELETE FROM excursion_reports')
    rows=c.execute('''SELECT r.shipment_id,r.reading_id,r.reading_time,r.temperature,p.policy_id,p.min_temperature,p.max_temperature,p.allowed_duration_minutes
      FROM temperature_readings r JOIN shipments s ON s.shipment_id=r.shipment_id
      JOIN lots l ON l.lot_id=s.lot_id JOIN threshold_policies p ON p.product_id=l.product_id
      WHERE datetime(r.reading_time)>=datetime(p.effective_from)
      AND (p.effective_to IS NULL OR datetime(r.reading_time)<datetime(p.effective_to))
      ORDER BY r.shipment_id,p.policy_id,r.reading_time''').fetchall()
    # Group key includes shipment and policy: excursions cannot cross shipment boundaries.
    active={}; reports=[]; seq=0
    for ship,rid,when,temp,policy,lo,hi,allowed in rows:
        key=(ship,policy); outside=temp<lo or temp>hi
        if outside:
            run=active.setdefault(key,[])
            if run and (datetime.fromisoformat(when)-datetime.fromisoformat(run[-1][1])).total_seconds()>600:
                seq+=1; reports.append(_report(seq,ship,policy,run)); active[key]=[]
            active[key].append((rid,when,allowed))
        elif key in active and active[key]:
            seq+=1; reports.append(_report(seq,ship,policy,active[key])); active[key]=[]
    for (ship,policy),run in active.items():
        if run:
            seq+=1; reports.append(_report(seq,ship,policy,run))
    c.executemany('INSERT INTO excursion_reports VALUES (?,?,?,?,?,?,?,?,?,?)',reports)
    con.commit(); con.close(); return len(reports)

def _report(seq,ship,policy,run):
    start=datetime.fromisoformat(run[0][1]); end=datetime.fromisoformat(run[-1][1])
    duration=int((end-start).total_seconds()/60)+10
    allowed=run[0][2]; severity='LOW' if duration<=10 else 'MEDIUM' if duration<=30 else 'HIGH' if duration<=60 else 'CRITICAL'
    decision='WITHIN_ALLOWANCE' if duration<=allowed else 'NON_COMPLIANT'
    return (f'EXCR-2026-{seq:06d}',ship,policy,run[0][1],run[-1][1],duration,severity,run[0][0],run[-1][0],decision)
if __name__=='__main__': print('Excursion reports generated:',detect())
