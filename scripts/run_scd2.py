"""Прогон sql/scd2_demo.sql — демо SCD2."""
import duckdb
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "retail.duckdb"
SQL_FILE = ROOT / "sql" / "scd2_demo.sql"

con = duckdb.connect(str(DB))
text = SQL_FILE.read_text(encoding="utf-8")

parts = re.split(r"--\s*=+", text)
queries = [p.strip() for p in parts if p.strip()
           and any(k in p.upper() for k in ("SELECT", "UPDATE", "INSERT"))]

for i, q in enumerate(queries, 1):
    print(f"\n{'='*60}")
    print(f"Шаг {i}")
    print('='*60)
    try:
        df = con.execute(q).df()
        if not df.empty:
            print(df.to_string(index=False))
        else:
            print("(нет строк)")
    except Exception as e:
        print(f"ОШИБКА: {e}")

con.close()