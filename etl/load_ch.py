"""
З07. Загрузка витрины в ClickHouse (constellation: 3 факта + 5 измерений).
Идемпотентно: TRUNCATE TABLE перед каждой загрузкой.
Порядок: dim → fact.
"""
import clickhouse_connect
from pathlib import Path
import csv
from datetime import date, datetime
import sys

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
DDL = ROOT / "sql" / "ddl_clickhouse.sql"

CH_HOST = "localhost"
CH_PORT = 8123
CH_USER = "default"
CH_PASSWORD = ""
CH_DATABASE = "retail_dw"

# Порядок удаления: сначала факты (у них FK), потом dims
TABLES = (
    "fact_sales", "fact_supplies", "fact_disposals",
    "dim_store", "dim_product", "dim_date", "dim_customer", "dim_reason",
)


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
    print("=== DDL ===")
    sql = DDL.read_text(encoding="utf-8")
    for stmt in sql.split(";"):
        stmt = stmt.strip()
        if not stmt:
            continue
        clean = "\n".join(l for l in stmt.splitlines() if not l.strip().startswith("--")).strip()
        if clean:
            client.command(clean)
    print("  ok")


def truncate_all(client):
    print("\n=== DROP TABLE ===")
    for t in TABLES:
        client.command(f"DROP TABLE IF EXISTS {t}")
        print(f"  dropped {t}")


def load_csv(client, table, csv_path, columns):
    """Загрузить CSV через client.insert() с конвертацией типов."""
    print(f"  loading {table}...")
    rows = []
    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            row = []
            for c in columns:
                val = r[c]
                # конвертация по имени колонки
                if c in ("full_date", "valid_from", "valid_to"):
                    if val == "" or val is None:
                        row.append(None)
                    else:
                        row.append(datetime.strptime(val, "%Y-%m-%d").date())
                elif c in ("is_current",):
                    row.append(val.lower() in ("true", "1"))
                elif c in ("store_id", "product_id", "customer_id",
                           "date_id", "qty", "reason_id", "version_id"):
                    row.append(int(val))
                elif c in ("sale_id", "supply_id", "disposal_id"):
                    row.append(int(val))
                elif c in ("amount", "cost", "cost_loss"):
                    row.append(float(val) if val else 0.0)
                else:
                    row.append(val)
            rows.append(row)
    client.insert(table, rows, column_names=columns)
    print(f"    {len(rows)} rows")


def load(client):
    print("\n=== Загрузка ===")

    # dims
    load_csv(client, "dim_store", RAW / "dim_store.csv",
             ["store_id", "store_name", "city", "region"])

    # dim_product — SCD2 (CSV только бизнес-колонки)
    print("  loading dim_product (SCD2)...")
    with open(RAW / "dim_product.csv", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = []
        for i, r in enumerate(reader, start=1):
            rows.append([
                i, int(r["product_id"]), r["product_name"],
                r["category"], r["brand"],
                date(2024, 1, 1), None, True,
            ])
    client.insert("dim_product", rows,
                  column_names=["version_id", "product_id", "product_name",
                                "category", "brand", "valid_from", "valid_to", "is_current"])
    print(f"    {len(rows)} rows")

    load_csv(client, "dim_date", RAW / "dim_date.csv",
             ["date_id", "full_date", "year", "month", "month_name", "day_of_week"])
    load_csv(client, "dim_customer", RAW / "dim_customer.csv",
             ["customer_id", "customer_name", "city", "loyalty_tier"])
    load_csv(client, "dim_reason", RAW / "dim_reason.csv",
             ["reason_id", "reason_name"])

    # facts
    load_csv(client, "fact_sales", RAW / "fact_sales.csv",
             ["sale_id", "date_id", "store_id", "product_id", "customer_id", "qty", "amount"])
    load_csv(client, "fact_supplies", RAW / "fact_supplies.csv",
             ["supply_id", "date_id", "store_id", "product_id", "qty", "cost"])
    load_csv(client, "fact_disposals", RAW / "fact_disposals.csv",
             ["disposal_id", "date_id", "store_id", "product_id", "reason_id", "qty", "cost_loss"])


def run_checks(client):
    print("\n=== Проверки ===")

    n = client.command("SELECT count() FROM fact_sales")
    check(n > 0, f"fact_sales: count = {n}")

    n = client.command("SELECT count() FROM fact_sales WHERE amount < 0 OR qty < 0")
    check(n == 0, f"fact_sales: отрицательных = {n}")

    n = client.command("SELECT count() FROM fact_disposals WHERE cost_loss < 0")
    check(n == 0, f"fact_disposals: отрицательных = {n}")


def print_summary(client):
    print("\n=== Counts ===")
    for t in TABLES:
        n = client.command(f"SELECT count() FROM {t}")
        print(f"  {t}: {n:,}")

    rev = client.command("SELECT sum(amount) FROM fact_sales")
    sup = client.command("SELECT sum(cost) FROM fact_supplies")
    dis = client.command("SELECT sum(cost_loss) FROM fact_disposals")
    print(f"\n=== Метрики ===")
    print(f"  Оборот:   {rev}")
    print(f"  Поставки: {sup}")
    print(f"  Потери:   {dis}")


def main():
    try:
        client = get_client()
        client.command("SELECT 1")
    except Exception as e:
        print(f"❌ Не удалось подключиться к ClickHouse: {e}")
        sys.exit(1)

    try:
        truncate_all(client)
        apply_ddl(client)
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