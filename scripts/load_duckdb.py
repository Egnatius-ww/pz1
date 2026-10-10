"""
Загрузка сырья из data/raw/ в DuckDB + проверки.
Идемпотентно. Запуск: py scripts/load_duckdb.py
"""
import duckdb
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
DB = ROOT / "data" / "retail.duckdb"
DDL = ROOT / "sql" / "ddl_duckdb.sql"


def main():
    con = duckdb.connect(str(DB))

    # 1. DDL — создаём таблицы
    con.execute(DDL.read_text(encoding="utf-8"))

    # 2. Очистка перед загрузкой (идемпотентность)
    for t in ("fact_sales", "dim_store", "dim_product", "dim_date"):
        con.execute(f"DELETE FROM {t}")

    # 3. Загрузка CSV
    con.execute(f"COPY dim_store   FROM '{RAW / 'dim_store.csv'}'   (HEADER, DELIMITER ',')")
    con.execute(f"COPY dim_product FROM '{RAW / 'dim_product.csv'}' (HEADER, DELIMITER ',')")
    con.execute(f"COPY dim_date    FROM '{RAW / 'dim_date.csv'}'    (HEADER, DELIMITER ',')")
    con.execute(f"COPY fact_sales  FROM '{RAW / 'fact_sales.csv'}'  (HEADER, DELIMITER ',')")

    # 4. Проверки
    print("=== SHOW TABLES ===")
    for (name,) in con.execute("SHOW TABLES").fetchall():
        print(f"  {name}")

    print("\n=== Counts ===")
    for t in ("fact_sales", "dim_store", "dim_product", "dim_date"):
        n = con.execute(f"SELECT count() FROM {t}").fetchone()[0]
        print(f"  {t}: {n}")

    print("\n=== Sum(amount) ===")
    rev = con.execute("SELECT sum(amount) FROM fact_sales").fetchone()[0]
    print(f"  Оборот: {rev}")

    print("\n=== Orphan FK (anti-join) ===")
    orphans = con.execute("""
        SELECT count()
        FROM fact_sales f
        LEFT JOIN dim_store   s ON f.store_id   = s.store_id
        LEFT JOIN dim_product p ON f.product_id = p.product_id
        LEFT JOIN dim_date    d ON f.date_id    = d.date_id
        WHERE s.store_id   IS NULL
           OR p.product_id IS NULL
           OR d.date_id    IS NULL
    """).fetchone()[0]
    print(f"  fact_sales-сироты: {orphans}")

    con.close()
    print(f"\nOK → {DB}")


if __name__ == "__main__":
    main()