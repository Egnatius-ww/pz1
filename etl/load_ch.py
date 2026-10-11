"""
З07. Загрузка витрины в ClickHouse (HTTP-порт 8123).
Идемпотентно: TRUNCATE TABLE перед каждой загрузкой.
Порядок: dim → fact.
База: retail_dw (совпадает с тем, куда init_ch.sh залил sample).
"""
import clickhouse_connect
from pathlib import Path
import csv
from datetime import date
import sys

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
DDL = ROOT / "sql" / "ddl_clickhouse.sql"

CH_HOST = "localhost"
CH_PORT = 8123              # ← HTTP, не 9000
CH_USER = "default"
CH_PASSWORD = ""
CH_DATABASE = "retail_dw"   # ← та же БД, что создаёт init_ch.sh

TABLES_ORDER = ("dim_store", "dim_product", "dim_date", "fact_sales")


class CheckFailed(Exception):
    pass


def check(cond: bool, msg: str) -> None:
    if not cond:
        raise CheckFailed(msg)
    print(f"  ✓ {msg}")


def get_client():
    return clickhouse_connect.get_client(
        host=CH_HOST, port=CH_PORT,
        username=CH_USER, password=CH_PASSWORD,
        database=CH_DATABASE,
    )


def apply_ddl(client):
    """Создать таблицы (IF NOT EXISTS). Разбиваем файл по ';' и выполняем по одному."""
    print("=== DDL ===")
    sql = DDL.read_text(encoding="utf-8")
    for stmt in sql.split(";"):
        stmt = stmt.strip()
        # пропускаем пустые и чисто комментарии
        if not stmt:
            continue
        # убираем комментарии в начале блока
        lines = [l for l in stmt.splitlines() if not l.strip().startswith("--")]
        clean = "\n".join(lines).strip()
        if clean:
            client.command(clean)
    print("  ok")


def truncate_all(client):
    print("\n=== TRUNCATE ===")
    for t in TABLES_ORDER:
        client.command(f"TRUNCATE TABLE IF EXISTS {t}")
        print(f"  truncated {t}")


def load_csv(client, table: str, csv_path: Path, columns: list):
    print(f"  loading {table}...")
    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = [[r[c] for c in columns] for r in reader]
    client.insert(table, rows, column_names=columns)
    print(f"    {len(rows)} rows")


def load(client):
    print("\n=== Загрузка ===")

    # dim_store
    load_csv(client, "dim_store", RAW / "dim_store.csv",
             ["store_id", "store_name", "city", "region"])

    # dim_product — SCD2: CSV не содержит version/valid, добавляем программно
    print("  loading dim_product (SCD2)...")
    with open(RAW / "dim_product.csv", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = []
        for i, r in enumerate(reader, start=1):
            rows.append([
                i,
                int(r["product_id"]),
                r["product_name"],
                r["category"],
                r["brand"],
                date(2024, 1, 1),
                None,
                True,
            ])
    client.insert("dim_product", rows,
                  column_names=["version_id", "product_id", "product_name",
                                "category", "brand", "valid_from",
                                "valid_to", "is_current"])
    print(f"    {len(rows)} rows")

    # dim_date
    # dim_date — конвертируем full_date в date
    print("  loading dim_date...")
    from datetime import datetime
    with open(RAW / "dim_date.csv", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = []
        for r in reader:
            rows.append([
                int(r["date_id"]),
                datetime.strptime(r["full_date"], "%Y-%m-%d").date(),
                int(r["year"]),
                int(r["month"]),
                r["month_name"],
                int(r["day_of_week"]),
            ])
    client.insert("dim_date", rows,
                  column_names=["date_id", "full_date", "year", "month",
                                "month_name", "day_of_week"])
    print(f"    {len(rows)} rows")

    # fact_sales
    load_csv(client, "fact_sales", RAW / "fact_sales.csv",
             ["sale_id", "date_id", "store_id", "product_id", "qty", "amount"])


def run_checks(client):
    print("\n=== Проверки ===")

    n = client.command("SELECT count() FROM fact_sales")
    check(n > 0, f"fact_sales: count = {n}")

    n = client.command(
        "SELECT count() FROM fact_sales WHERE amount < 0 OR qty < 0"
    )
    check(n == 0, f"fact_sales: отрицательных qty/amount = {n}")

    # Сироты — в CH LEFT JOIN даёт значения по умолчанию (0), а не NULL,
    # поэтому проверяем через NOT IN
    n = client.command("""
        SELECT count() FROM fact_sales
        WHERE store_id NOT IN (SELECT store_id FROM dim_store)
           OR product_id NOT IN (SELECT product_id FROM dim_product)
           OR date_id NOT IN (SELECT date_id FROM dim_date)
    """)
    check(n == 0, f"fact_sales: сирот FK = {n}")


def print_summary(client):
    print("\n=== Counts ===")
    for t in TABLES_ORDER:
        n = client.command(f"SELECT count() FROM {t}")
        print(f"  {t}: {n}")

    rev = client.command("SELECT sum(amount) FROM fact_sales")
    print(f"\n=== Sum(amount) ===\n  Оборот: {rev}")


def main():
    try:
        client = get_client()
        client.command("SELECT 1")
    except Exception as e:
        print(f"❌ Не удалось подключиться к ClickHouse: {e}")
        print("Проверь: docker compose ps, curl.exe http://localhost:8123/ping")
        sys.exit(1)

    try:
        apply_ddl(client)
        truncate_all(client)
        load(client)
        run_checks(client)
        print_summary(client)
    except CheckFailed as e:
        print(f"\n❌ ЗАГРУЗКА ОСТАНОВЛЕНА: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ОШИБКА: {e}")
        sys.exit(1)

    print("\n✓ Загрузка в ClickHouse успешна")


if __name__ == "__main__":
    main()