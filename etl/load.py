"""
З05. ELT: загрузка сырья в DuckDB + проверки качества.
Constellation: 3 факта + 5 измерений.

Порядок:
  1. Удалить старый файл БД
  2. DDL из sql/ddl_duckdb.sql
  3. Загрузка: dim → fact
  4. Проверки качества

Запуск: py etl/load.py
"""
import sys
import duckdb
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
DB = ROOT / "data" / "retail.duckdb"
DDL = ROOT / "sql" / "ddl_duckdb.sql"

TABLES = ("fact_sales", "fact_supplies", "fact_disposals",
          "dim_store", "dim_product", "dim_date",
          "dim_customer", "dim_reason")


class CheckFailed(Exception):
    pass


def check(condition: bool, msg: str) -> None:
    if not condition:
        raise CheckFailed(msg)
    print(f"  ✓ {msg}")


def run_checks(con: duckdb.DuckDBPyConnection) -> None:
    print("\n=== Проверки качества ===")

    # 1. Пустые ключи в fact_sales
    n = con.execute("""
        SELECT count() FROM fact_sales
        WHERE date_id IS NULL OR store_id IS NULL
           OR product_id IS NULL OR customer_id IS NULL
           OR qty IS NULL OR amount IS NULL
    """).fetchone()[0]
    check(n == 0, f"fact_sales: пустых ключей/сумм = {n}")

    # 2. Отрицательные значения
    n = con.execute("""
        SELECT count() FROM fact_sales
        WHERE qty < 0 OR amount < 0
    """).fetchone()[0]
    check(n == 0, f"fact_sales: отрицательных = {n}")

    n = con.execute("""
        SELECT count() FROM fact_supplies WHERE qty < 0 OR cost < 0
    """).fetchone()[0]
    check(n == 0, f"fact_supplies: отрицательных = {n}")

    n = con.execute("""
        SELECT count() FROM fact_disposals WHERE qty < 0 OR cost_loss < 0
    """).fetchone()[0]
    check(n == 0, f"fact_disposals: отрицательных = {n}")

    # 3. Старые даты
    n = con.execute("SELECT count() FROM dim_date WHERE year < 2000").fetchone()[0]
    check(n == 0, f"dim_date: дат раньше 2000 = {n}")

    # 4. Сироты FK в fact_sales
    n = con.execute("""
        SELECT count()
        FROM fact_sales f
        LEFT JOIN dim_store    s ON f.store_id    = s.store_id
        LEFT JOIN dim_product  p ON f.product_id  = p.product_id
        LEFT JOIN dim_date     d ON f.date_id     = d.date_id
        LEFT JOIN dim_customer c ON f.customer_id = c.customer_id
        WHERE s.store_id IS NULL OR p.product_id IS NULL
           OR d.date_id IS NULL OR c.customer_id IS NULL
    """).fetchone()[0]
    check(n == 0, f"fact_sales: сирот FK = {n}")

    # 5. Сироты FK в fact_disposals (с reason_id)
    n = con.execute("""
        SELECT count()
        FROM fact_disposals f
        LEFT JOIN dim_reason r ON f.reason_id = r.reason_id
        WHERE r.reason_id IS NULL
    """).fetchone()[0]
    check(n == 0, f"fact_disposals: сирот reason_id = {n}")


def apply_ddl(con: duckdb.DuckDBPyConnection) -> None:
    con.execute(DDL.read_text(encoding="utf-8"))


def load(con):
    print("\n=== Загрузка ===")

    # --- dim_store ---
    print("  dim_store...")
    con.execute(f"COPY dim_store FROM '{RAW / 'dim_store.csv'}' (HEADER, DELIMITER ',')")

    # --- dim_product (SCD2 через staging) ---
    print("  dim_product (staging → SCD2)...")
    con.execute(f"""
        CREATE OR REPLACE TEMP TABLE stg_product AS
        SELECT * FROM read_csv_auto('{RAW / 'dim_product.csv'}', header=true)
    """)
    con.execute("""
        INSERT INTO dim_product
            (version_id, product_id, product_name, category, brand,
             valid_from, valid_to, is_current)
        SELECT
            row_number() OVER (ORDER BY product_id) AS version_id,
            product_id, product_name, category, brand,
            DATE '2024-01-01' AS valid_from,
            NULL AS valid_to,
            TRUE AS is_current
        FROM stg_product
    """)

    # --- dim_date ---
    print("  dim_date...")
    con.execute(f"COPY dim_date FROM '{RAW / 'dim_date.csv'}' (HEADER, DELIMITER ',')")

    # --- dim_customer ---
    print("  dim_customer...")
    con.execute(f"COPY dim_customer FROM '{RAW / 'dim_customer.csv'}' (HEADER, DELIMITER ',')")

    # --- dim_reason ---
    print("  dim_reason...")
    con.execute(f"COPY dim_reason FROM '{RAW / 'dim_reason.csv'}' (HEADER, DELIMITER ',')")

    # --- fact_sales ---
    print("  fact_sales...")
    con.execute(f"COPY fact_sales FROM '{RAW / 'fact_sales.csv'}' (HEADER, DELIMITER ',')")

    # --- fact_supplies ---
    print("  fact_supplies...")
    con.execute(f"COPY fact_supplies FROM '{RAW / 'fact_supplies.csv'}' (HEADER, DELIMITER ',')")

    # --- fact_disposals ---
    print("  fact_disposals...")
    con.execute(f"COPY fact_disposals FROM '{RAW / 'fact_disposals.csv'}' (HEADER, DELIMITER ',')")


def print_summary(con: duckdb.DuckDBPyConnection) -> None:
    print("\n=== Counts ===")
    for t in TABLES:
        n = con.execute(f"SELECT count() FROM {t}").fetchone()[0]
        print(f"  {t}: {n:,}")

    rev = con.execute("SELECT sum(amount) FROM fact_sales").fetchone()[0]
    sup = con.execute("SELECT sum(cost) FROM fact_supplies").fetchone()[0]
    dis = con.execute("SELECT sum(cost_loss) FROM fact_disposals").fetchone()[0]
    print(f"\n=== Метрики ===")
    print(f"  Оборот:   {rev}")
    print(f"  Поставки: {sup}")
    print(f"  Потери:   {dis}")


def main() -> None:
    # Удаляем старый файл БД
    if DB.exists():
        DB.unlink()
        print(f"=== Удалён старый файл: {DB} ===")

    con = duckdb.connect(str(DB))
    con.execute("SET preserve_insertion_order = false;")

    print("\n=== DDL ===")
    apply_ddl(con)
    print("  ok")

    load(con)

    try:
        run_checks(con)
    except CheckFailed as e:
        print(f"\n❌ ЗАГРУЗКА ОСТАНОВЛЕНА: {e}")
        con.close()
        sys.exit(1)

    print_summary(con)

    con.close()
    print(f"\n✓ Загрузка успешна → {DB}")


if __name__ == "__main__":
    main()