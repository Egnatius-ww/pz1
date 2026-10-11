"""
З07. Сверка DuckDB ↔ ClickHouse:
- count(fact_sales)
- sum(amount) — главная метрика

Расхождение — сигнал, что загрузка потеряла или задвоила строки.
"""
import duckdb
import clickhouse_connect
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DUCK_DB = ROOT / "data" / "retail.duckdb"

CH_HOST = "localhost"
CH_PORT = 8123
CH_USER = "default"
CH_PASSWORD = ""
CH_DATABASE = "retail_dw"


def main():
    duck = duckdb.connect(str(DUCK_DB))
    ch = clickhouse_connect.get_client(
        host=CH_HOST, port=CH_PORT,
        username=CH_USER, password=CH_PASSWORD,
        database=CH_DATABASE,
    )

    print("=== DuckDB vs ClickHouse ===\n")

    checks = [
        ("count(fact_sales)", "SELECT count() FROM fact_sales"),
        ("sum(amount)",       "SELECT sum(amount) FROM fact_sales"),
    ]

    all_ok = True
    for label, query in checks:
        d = duck.execute(query).fetchone()[0]
        c = ch.command(query)

        # приводим к одному типу для сравнения (Decimal vs float)
        d_str = str(d).rstrip("0").rstrip(".") if "." in str(d) else str(d)
        c_str = str(c).rstrip("0").rstrip(".") if "." in str(c) else str(c)

        ok = d_str == c_str
        all_ok = all_ok and ok
        mark = "✓" if ok else "❌ РАСХОЖДЕНИЕ"

        print(f"{label}")
        print(f"  DuckDB:     {d}")
        print(f"  ClickHouse: {c}")
        print(f"  {mark}\n")

    duck.close()

    if all_ok:
        print("✓ Все проверки пройдены — числа совпадают")
    else:
        print("❌ Есть расхождения — разбирайся с загрузкой")


if __name__ == "__main__":
    main()