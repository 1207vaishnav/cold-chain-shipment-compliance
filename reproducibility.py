import sqlite3,hashlib,json,subprocess,sys,tempfile
from pathlib import Path
BASE=Path(__file__).resolve().parent
TABLES=['products','lots','shipments','packaging','loggers','logger_assignments','temperature_readings','custody_events','route_stops','threshold_policies','anomaly_issues']
def fingerprint(db):
    con=sqlite3.connect(db); result={}
    for table in TABLES:
        digest=hashlib.sha256(); count=0
        for row in con.execute(f'SELECT * FROM {table} ORDER BY 1'):
            digest.update(json.dumps(row,separators=(',',':')).encode()); count+=1
        result[table]={'rows':count,'sha256':digest.hexdigest()}
    con.close(); return result
def run():
    with tempfile.TemporaryDirectory() as folder:
        a=Path(folder)/'a.db'; b=Path(folder)/'b.db'
        for target in (a,b):
            subprocess.run([sys.executable,str(BASE/'data_generator.py'),'--shipments','20','--loggers','5','--seed','20261022','--db',str(target)],check=True,capture_output=True,text=True)
        first,second=fingerprint(a),fingerprint(b); passed=first==second
        print(json.dumps({'reproducible':passed,'first':first,'second':second},indent=2)); return passed
if __name__=='__main__': raise SystemExit(0 if run() else 1)
