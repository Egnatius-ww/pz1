"""
З09. Создать MV daily_store_revenue и заполнить её из fact_sales.
Запуск: py scripts/setup_z09.py
"""
import clickhouse_connect
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SQL_FILE = ROOT / "sql" / "mv_daily_store.sql"

client = clickhouse_connect.get_client(
    host="localhost", port=8123,
    username="default", password="",
    database="retail_dw",
)

# 1. Выполнить DDL из файла
print("=== 1. Создание MV и таблицы ===")
sql = SQL_FILE.read_text(encoding="utf-8")
for stmt in sql.split(";"):
    stmt = stmt.strip()
    if not stmt:
        continue
    # убираем строчные комментарии
    clean = "\n".join(
        line for line in stmt.splitlines()
        if not line.strip().startswith("--")
    ).strip()
    if clean:
        client.command(clean)
        print(f"  ✓ выполнен блок ({clean[:40]}...)")

# 2. Первичное заполнение сводки
print("\n=== 2. Заполнение daily_store_revenue ===")
client.command("TRUNCATE TABLE IF EXISTS daily_store_revenue")
client.command("""
    INSERT INTO daily_store_revenue
    SELECT
        dd.full_date,
        fs.store_id,
        sum(fs.amount)
    FROM fact_sales fs
    JOIN dim_date dd ON fs.date_id = dd.date_id
    GROUP BY dd.full_date, fs.store_id
""")
n = client.command("SELECT count() FROM daily_store_revenue")
print(f"  daily_store_revenue: {n} строк")

client.close()
print("\n✓ Готово")