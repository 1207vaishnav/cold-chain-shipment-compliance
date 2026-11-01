import sqlite3,csv,json
from pathlib import Path
from config import DATABASE_NAME,OUTPUT_DIRECTORY
BASE=Path(__file__).resolve().parent
TABLES=['products','lots','shipments','packaging','loggers','logger_assignments','temperature_readings','custody_events','route_stops','threshold_policies','excursion_reports','shipment_status_history','anomaly_issues','compliance_reports']
def export(db_path=BASE/DATABASE_NAME):
    out=BASE/OUTPUT_DIRECTORY; out.mkdir(exist_ok=True); con=sqlite3.connect(db_path)
    for table in TABLES:
        cur=con.execute(f'SELECT * FROM {table}'); cols=[x[0] for x in cur.description]
        with open(out/f'{table}.csv','w',newline='',encoding='utf-8') as f:
            w=csv.writer(f); w.writerow(cols); w.writerows(cur)
        cur=con.execute(f'SELECT * FROM {table}')
        with open(out/f'{table}.json','w',encoding='utf-8') as f:
            f.write('['); first=True
            for row in cur:
                if not first: f.write(',')
                json.dump(dict(zip(cols,row)),f,separators=(',',':'))
                first=False
            f.write(']')
    con.close(); print(f'Exported {len(TABLES)} tables as CSV and JSON to {out}')
if __name__=='__main__': export()
