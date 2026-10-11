"""З08. Прогон queries/p08_ch.sql в ClickHouse."""
import clickhouse_connect
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent.parent
SQL_FILE = ROOT / "queries" / "p08_ch.sql"

client = clickhouse_connect.get_client(
    host="localhost", port=8123,
    username="default", password="",
    database="retail_dw",
)

text = SQL_FILE.read_text(encoding="utf-8")
parts = re.split(r"--\s*=+", text)
queries = [p.strip() for p in parts if p.strip() and "SELECT" in p.upper()]

for i, q in enumerate(queries, 1):
    print(f"\n{'='*60}")
    print(f"Запрос {i}")
    print('='*60)
    try:
        result = client.query(q)
        print(" | ".join(result.column_names))
        print("-" * 60)
        for row in result.result_rows:
            print(" | ".join(str(v) for v in row))
        print(f"\n({len(result.result_rows)} строк)")
    except Exception as e:
        print(f"ОШИБКА: {e}")

client.close()