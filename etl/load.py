"""
З05. ELT: загрузка сырья в DuckDB + проверки качества.

Порядок:
  1. DDL из sql/ddl_duckdb.sql
  2. DELETE FROM всех таблиц (идемпотентность)
  3. COPY: сначала справочники (dim_*), потом факт (fact_sales)
  4. Проверки качества — при провале откат и exit 1

Запуск: py etl/load.py
"""
import sys
import duckdb
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
DB = ROOT / "data" / "retail.duckdb"
DDL = ROOT / "sql" / "ddl_duckdb.sql"

TABLES = ("fact_sales", "dim_store", "dim_product", "dim_date")


class CheckFailed(Exception):
    """Проверка качества не прошла — загрузка останавливается."""
    pass


def check(condition: bool, msg: str) -> None:
    """Если condition False — бросаем CheckFailed."""
    if not condition:
        raise CheckFailed(msg)
    print(f"  ✓ {msg}")


def run_checks(con: duckdb.DuckDBPyConnection) -> None:
    """Все проверки качества после загрузки."""
    print("\n=== Проверки качества ===")

    # 1. Пустые ключи и суммы
    n = con.execute("""
        SELECT count() FROM fact_sales
        WHERE date_id IS NULL
           OR store_id IS NULL
           OR product_id IS NULL
           OR qty IS NULL
           OR amount IS NULL
    """).fetchone()[0]
    check(n == 0, f"fact_sales: пустых ключей/сумм = {n}")

    # 2. Странный диапазон: qty >= 0, amount >= 0
    n = con.execute("""
        SELECT count() FROM fact_sales
        WHERE qty < 0 OR amount < 0
    """).fetchone()[0]
    check(n == 0, f"fact_sales: отрицательных qty/amount = {n}")

    # 2b. Старые даты
    n = con.execute("""
        SELECT count() FROM dim_date WHERE year < 2000
    """).fetchone()[0]
    check(n == 0, f"dim_date: дат раньше 2000 = {n}")

    # 3. Дубли по grain (sale_id — PK)
    n = con.execute("""
        SELECT count() FROM (
            SELECT sale_id FROM fact_sales
            GROUP BY sale_id HAVING count() > 1
        )
    """).fetchone()[0]
    check(n == 0, f"fact_sales: дублей sale_id = {n}")

    # 4. Сироты FK (anti-join)
    n = con.execute("""
        SELECT count()
        FROM fact_sales f
        LEFT JOIN dim_store   s ON f.store_id   = s.store_id
        LEFT JOIN dim_product p ON f.product_id = p.product_id
        LEFT JOIN dim_date    d ON f.date_id    = d.date_id
        WHERE s.store_id IS NULL
           OR p.product_id IS NULL
           OR d.date_id IS NULL
    """).fetchone()[0]
    check(n == 0, f"fact_sales: сирот FK = {n}")


def cleanup(con: duckdb.DuckDBPyConnection) -> None:
    """Очистка таблиц — для идемпотентности и отката."""
    for t in TABLES:
        con.execute(f"DELETE FROM {t}")


def load(con):
    """Загрузка CSV: dim → fact. dim_product — через staging + трансформация в SCD2."""
    print("\n=== Загрузка ===")

    # --- dim_store: SCD1, как было ---
    print("  dim_store...")
    con.execute(f"COPY dim_store FROM '{RAW / 'dim_store.csv'}' (HEADER, DELIMITER ',')")

    # --- dim_product: SCD2 через staging ---
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
            product_id,
            product_name,
            category,
            brand,
            DATE '2024-01-01' AS valid_from,
            NULL              AS valid_to,
            TRUE              AS is_current
        FROM stg_product
    """)

    # --- dim_date: как было ---
    print("  dim_date...")
    con.execute(f"COPY dim_date FROM '{RAW / 'dim_date.csv'}' (HEADER, DELIMITER ',')")

    # --- fact_sales: как было ---
    print("  fact_sales...")
    con.execute(f"COPY fact_sales FROM '{RAW / 'fact_sales.csv'}' (HEADER, DELIMITER ',')")


def print_summary(con: duckdb.DuckDBPyConnection) -> None:
    """Печать финальных чисел."""
    print("\n=== Counts ===")
    for t in TABLES:
        n = con.execute(f"SELECT count() FROM {t}").fetchone()[0]
        print(f"  {t}: {n}")

    rev = con.execute("SELECT sum(amount) FROM fact_sales").fetchone()[0]
    print(f"\n=== Sum(amount) ===\n  Оборот: {rev}")


def main() -> None:
    con = duckdb.connect(str(DB))

    # 1. DDL — структура
    print("=== DDL ===")
    con.execute(DDL.read_text(encoding="utf-8"))
    print("  ok")

    # 2. Очистка перед загрузкой (идемпотентность)
    print("\n=== Очистка таблиц ===")
    cleanup(con)
    for t in TABLES:
        print(f"  cleaned {t}")

    # 3. Загрузка (dim → fact)
    load(con)

    # 4. Проверки — при провале откат и exit
    try:
        run_checks(con)
    except CheckFailed as e:
        print(f"\n❌ ЗАГРУЗКА ОСТАНОВЛЕНА: {e}")
        print("Откатываю изменения (DELETE FROM всех таблиц)...")
        cleanup(con)
        con.close()
        sys.exit(1)

    # 5. Итог
    print_summary(con)

    con.close()
    print(f"\n✓ Загрузка успешна → {DB}")


if __name__ == "__main__":
    main()