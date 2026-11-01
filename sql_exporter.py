
import sqlite3
from pathlib import Path
from config import DATABASE_NAME, OUTPUT_DIRECTORY

BASE = Path(__file__).resolve().parent

def export(db_path=BASE / DATABASE_NAME):
    out = BASE / OUTPUT_DIRECTORY
    out.mkdir(parents=True, exist_ok=True)

    path = out / "cold_chain_seed.sql"
    con = sqlite3.connect(db_path)

    try:
        with open(path, "w", encoding="utf-8") as f:
            for statement in con.iterdump():
                f.write(statement + "\n")
    finally:
        con.close()

    print("SQL export:", path)

if __name__ == "__main__":
    export()
