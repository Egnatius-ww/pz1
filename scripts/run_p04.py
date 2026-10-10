"""Прогон queries/p04.sql — все запросы по порядку."""
import duckdb
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "retail.duckdb"
SQL_FILE = ROOT / "queries" / "p04.sql"

con = duckdb.connect(str(DB))
text = SQL_FILE.read_text(encoding="utf-8")

# разбиваем по блокам комментариев -- ====
parts = re.split(r"--\s*=+", text)
queries = [p.strip() for p in parts if p.strip() and "SELECT" in p.upper()]

for i, q in enumerate(queries, 1):
    print(f"\n{'='*60}")
    print(f"Запрос {i}")
    print('='*60)
    try:
        df = con.execute(q).df()
        print(df.to_string(index=False))
    except Exception as e:
        print(f"ОШИБКА: {e}")

con.close()