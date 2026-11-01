import argparse
from pathlib import Path
from data_generator import generate
from excursion_detector import detect
from compliance_engine import run as compliance
from validator import validate
from exporter import export
from sql_exporter import export as export_sql

def main():
    p=argparse.ArgumentParser(description='Generate and evaluate synthetic cold-chain shipment compliance data')
    p.add_argument('--shipments',type=int,default=5000); p.add_argument('--loggers',type=int,default=1000)
    p.add_argument('--seed',type=int,default=20261022); p.add_argument('--db',default='cold_chain.db')
    p.add_argument('--skip-export',action='store_true'); args=p.parse_args()
    print('Generation:',generate(args.shipments,args.loggers,args.seed,args.db,True))
    print('Excursion reports:',detect(args.db))
    print('Compliance reports:',compliance(args.db))
    validation = validate(args.db)

    print('Validation:', validation)

    if not validation['structural_checks_pass']:
        raise SystemExit(
            'Validation failed. Export cancelled.'
        )
    if not args.skip_export:
        export(args.db); export_sql(args.db)
if __name__=='__main__': main()
