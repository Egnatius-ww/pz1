"""
Генерация большого retail_dw в DuckDB (SQL-based).
Constellation-схема: 3 факта + 5 измерений.
Запуск: py scripts/generate_big_retail.py [--facts N] [--db PATH]
"""
import argparse
from pathlib import Path
import duckdb

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB = ROOT / "data" / "retail.duckdb"
RAW = ROOT / "data" / "raw"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--facts", type=int, default=2_000_000)
    parser.add_argument("--stores", type=int, default=50)
    parser.add_argument("--products", type=int, default=500)
    parser.add_argument("--customers", type=int, default=500)
    parser.add_argument("--years", type=int, default=1, help="сколько лет календаря")
    parser.add_argument("--db", default=str(DEFAULT_DB))
    args = parser.parse_args()

    db_path = Path(args.db).resolve()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    RAW.mkdir(parents=True, exist_ok=True)

    con = duckdb.connect(str(db_path))
    print(f"БД: {db_path}")

    # ---------- DROP ----------
    print("Пересоздаю таблицы...")
    for t in ("fact_sales", "fact_supplies", "fact_disposals",
              "dim_customer", "dim_reason", "dim_date",
              "dim_product", "dim_store"):
        con.execute(f"DROP TABLE IF EXISTS {t}")

    # ---------- DDL ----------
    con.execute("""
        CREATE TABLE dim_store (
            store_id    INTEGER PRIMARY KEY,
            store_name  VARCHAR NOT NULL,
            city        VARCHAR NOT NULL,
            region      VARCHAR NOT NULL
        )
    """)
    con.execute("""
        CREATE TABLE dim_product (
            version_id    INTEGER PRIMARY KEY,
            product_id    INTEGER NOT NULL,
            product_name  VARCHAR NOT NULL,
            category      VARCHAR,
            brand         VARCHAR,
            valid_from    DATE NOT NULL,
            valid_to      DATE,
            is_current    BOOLEAN NOT NULL DEFAULT TRUE
        )
    """)
    con.execute("""
        CREATE TABLE dim_date (
            date_id      INTEGER PRIMARY KEY,
            full_date    DATE NOT NULL,
            year         INTEGER NOT NULL,
            month        INTEGER NOT NULL,
            month_name   VARCHAR NOT NULL,
            day_of_week  INTEGER NOT NULL
        )
    """)
    con.execute("""
        CREATE TABLE dim_customer (
            customer_id    INTEGER PRIMARY KEY,
            customer_name  VARCHAR NOT NULL,
            city           VARCHAR,
            loyalty_tier   VARCHAR
        )
    """)
    con.execute("""
        CREATE TABLE dim_reason (
            reason_id    INTEGER PRIMARY KEY,
            reason_name  VARCHAR NOT NULL
        )
    """)
    con.execute("""
        CREATE TABLE fact_sales (
            sale_id     BIGINT PRIMARY KEY,
            date_id     INTEGER NOT NULL REFERENCES dim_date(date_id),
            store_id    INTEGER NOT NULL REFERENCES dim_store(store_id),
            product_id  INTEGER NOT NULL,
            customer_id INTEGER NOT NULL REFERENCES dim_customer(customer_id),
            qty         INTEGER NOT NULL,
            amount      DECIMAL(12,2) NOT NULL
        )
    """)
    con.execute("""
        CREATE TABLE fact_supplies (
            supply_id   BIGINT PRIMARY KEY,
            date_id     INTEGER NOT NULL REFERENCES dim_date(date_id),
            store_id    INTEGER NOT NULL REFERENCES dim_store(store_id),
            product_id  INTEGER NOT NULL,
            qty         INTEGER NOT NULL,
            cost        DECIMAL(12,2) NOT NULL
        )
    """)
    con.execute("""
        CREATE TABLE fact_disposals (
            disposal_id BIGINT PRIMARY KEY,
            date_id     INTEGER NOT NULL REFERENCES dim_date(date_id),
            store_id    INTEGER NOT NULL REFERENCES dim_store(store_id),
            product_id  INTEGER NOT NULL,
            reason_id   INTEGER NOT NULL REFERENCES dim_reason(reason_id),
            qty         INTEGER NOT NULL,
            cost_loss   DECIMAL(12,2) NOT NULL
        )
    """)

    # ---------- dim_store ----------
    print(f"dim_store: {args.stores}...")
    con.execute(f"""
        INSERT INTO dim_store
        SELECT
            i AS store_id,
            'Магазин-' || lpad(i::VARCHAR, 3, '0') AS store_name,
            CASE (i % 6)
                WHEN 0 THEN 'Минск' WHEN 1 THEN 'Гомель' WHEN 2 THEN 'Гродно'
                WHEN 3 THEN 'Брест' WHEN 4 THEN 'Витебск' ELSE 'Могилёв'
            END AS city,
            CASE (i % 4)
                WHEN 0 THEN 'Центр' WHEN 1 THEN 'Юг'
                WHEN 2 THEN 'Запад' ELSE 'Восток'
            END AS region
        FROM range(1, {args.stores + 1}) r(i)
    """)

    # ---------- dim_product ----------
    print(f"dim_product: {args.products}...")
    categories = ["Молочка", "Напитки", "Хлеб", "Бакалея", "Мясо",
                  "Овощи", "Фрукты", "Снеки", "Заморозка", "Бытовая химия"]
    cat_list = ",".join(f"'{c}'" for c in categories)
    con.execute(f"""
        INSERT INTO dim_product
        WITH cats AS (SELECT unnest([{cat_list}]) AS category),
        numbered AS (
            SELECT
                row_number() OVER () AS product_id,
                category
            FROM cats, range(1, {args.products // len(categories) + 1})
        )
        SELECT
            product_id AS version_id,
            product_id,
            category || ' товар #' || lpad(product_id::VARCHAR, 4, '0') AS product_name,
            category,
            'Brand' || ((product_id % 15) + 1)::VARCHAR AS brand,
            DATE '2024-01-01' AS valid_from,
            NULL::DATE AS valid_to,
            TRUE AS is_current
        FROM numbered
        LIMIT {args.products}
    """)

    # ---------- dim_date ----------
    years_end = 2024 + args.years - 1
    print(f"dim_date: 2024-01-01 .. {years_end}-12-31...")
    con.execute(f"""
        INSERT INTO dim_date
        SELECT
            CAST(strftime(d, '%Y%m%d') AS INTEGER) AS date_id,
            d::DATE AS full_date,
            year(d) AS year,
            month(d) AS month,
            CASE month(d)
                WHEN 1 THEN 'Январь' WHEN 2 THEN 'Февраль' WHEN 3 THEN 'Март'
                WHEN 4 THEN 'Апрель' WHEN 5 THEN 'Май' WHEN 6 THEN 'Июнь'
                WHEN 7 THEN 'Июль' WHEN 8 THEN 'Август' WHEN 9 THEN 'Сентябрь'
                WHEN 10 THEN 'Октябрь' WHEN 11 THEN 'Ноябрь' ELSE 'Декабрь'
            END AS month_name,
            dayofweek(d) AS day_of_week
        FROM generate_series(
            DATE '2024-01-01',
            DATE '{years_end}-12-31',
            INTERVAL 1 DAY
        ) t(d)
    """)

    total_days = args.years * 365

    # ---------- dim_customer ----------
    print(f"dim_customer: {args.customers}...")
    con.execute(f"""
        INSERT INTO dim_customer
        SELECT
            i AS customer_id,
            CASE (i % 8)
                WHEN 0 THEN 'Иван' WHEN 1 THEN 'Пётр' WHEN 2 THEN 'Анна'
                WHEN 3 THEN 'Мария' WHEN 4 THEN 'Сергей' WHEN 5 THEN 'Ольга'
                WHEN 6 THEN 'Дмитрий' ELSE 'Елена'
            END
            || ' '
            || CASE (i % 6)
                WHEN 0 THEN 'Иванов' WHEN 1 THEN 'Петров' WHEN 2 THEN 'Сидорова'
                WHEN 3 THEN 'Смирнов' WHEN 4 THEN 'Кузнецов' ELSE 'Попова'
            END
            || ' #' || i AS customer_name,
            CASE (i % 6)
                WHEN 0 THEN 'Минск' WHEN 1 THEN 'Гомель' WHEN 2 THEN 'Гродно'
                WHEN 3 THEN 'Брест' WHEN 4 THEN 'Витебск' ELSE 'Могилёв'
            END AS city,
            CASE (i % 4)
                WHEN 0 THEN 'Bronze' WHEN 1 THEN 'Silver'
                WHEN 2 THEN 'Gold' ELSE 'Platinum'
            END AS loyalty_tier
        FROM range(1, {args.customers + 1}) r(i)
    """)

    # ---------- dim_reason ----------
    print("dim_reason: 5...")
    con.execute("""
        INSERT INTO dim_reason VALUES
            (1, 'Истёк срок годности'),
            (2, 'Повреждение упаковки'),
            (3, 'Кража'),
            (4, 'Ошибка учёта'),
            (5, 'Бой при транспортировке')
    """)

    # ---------- fact_sales ----------
    print(f"fact_sales: {args.facts:,}...")
    con.execute(f"""
        INSERT INTO fact_sales
        WITH gen AS (
            SELECT
                i::BIGINT AS sale_id,
                CAST(strftime(
                    DATE '2024-01-01' + ((i * 37 + 11) % {total_days})::INTEGER,
                    '%Y%m%d'
                ) AS INTEGER) AS date_id,
                ((i * 19 + 3) % {args.stores} + 1)::INTEGER AS store_id,
                ((i * 17 + 29) % {args.products} + 1)::INTEGER AS product_id,
                ((i * 23 + 7) % {args.customers} + 1)::INTEGER AS customer_id,
                ((i * 11 + 2) % 8 + 1)::INTEGER AS qty
            FROM range(1, {args.facts + 1}) r(i)
        )
        SELECT
            sale_id, date_id, store_id, product_id, customer_id, qty,
            (qty * (1.5 + (product_id % 30) * 0.5))::DECIMAL(12,2) AS amount
        FROM gen
    """)

    # ---------- fact_supplies ----------
    print(f"fact_supplies: {args.facts // 10:,}...")
    con.execute(f"""
        INSERT INTO fact_supplies
        WITH gen AS (
            SELECT
                i::BIGINT AS supply_id,
                CAST(strftime(
                    DATE '2024-01-01' + ((i * 41 + 7) % {total_days})::INTEGER,
                    '%Y%m%d'
                ) AS INTEGER) AS date_id,
                ((i * 23 + 5) % {args.stores} + 1)::INTEGER AS store_id,
                ((i * 13 + 19) % {args.products} + 1)::INTEGER AS product_id,
                ((i * 7 + 3) % 50 + 10)::INTEGER AS qty
            FROM range(1, {args.facts // 10 + 1}) r(i)
        )
        SELECT
            supply_id, date_id, store_id, product_id, qty,
            (qty * (1.0 + (product_id % 20) * 0.3))::DECIMAL(12,2) AS cost
        FROM gen
    """)

    # ---------- fact_disposals ----------
    print(f"fact_disposals: {args.facts // 40:,}...")
    con.execute(f"""
        INSERT INTO fact_disposals
        WITH gen AS (
            SELECT
                i::BIGINT AS disposal_id,
                CAST(strftime(
                    DATE '2024-01-01' + ((i * 47 + 13) % {total_days})::INTEGER,
                    '%Y%m%d'
                ) AS INTEGER) AS date_id,
                ((i * 29 + 11) % {args.stores} + 1)::INTEGER AS store_id,
                ((i * 17 + 31) % {args.products} + 1)::INTEGER AS product_id,
                ((i * 11 + 7) % 5 + 1)::INTEGER AS reason_id,
                ((i * 7 + 5) % 10 + 1)::INTEGER AS qty
            FROM range(1, {args.facts // 40 + 1}) r(i)
        )
        SELECT
            disposal_id, date_id, store_id, product_id, reason_id, qty,
            (qty * (1.0 + (product_id % 20) * 0.3))::DECIMAL(12,2) AS cost_loss
        FROM gen
    """)

    # ---------- Проверки ----------
    print("\n=== Counts ===")
    for t in ("dim_store", "dim_product", "dim_date", "dim_customer",
              "dim_reason", "fact_sales", "fact_supplies", "fact_disposals"):
        n = con.execute(f"SELECT count() FROM {t}").fetchone()[0]
        print(f"  {t}: {n:,}")

    rev_sales = con.execute("SELECT round(sum(amount), 2) FROM fact_sales").fetchone()[0]
    rev_sup = con.execute("SELECT round(sum(cost), 2) FROM fact_supplies").fetchone()[0]
    rev_dis = con.execute("SELECT round(sum(cost_loss), 2) FROM fact_disposals").fetchone()[0]
    print(f"\n=== Метрики ===")
    print(f"  Оборот (sales):    {rev_sales}")
    print(f"  Поставки (cost):   {rev_sup}")
    print(f"  Потери (cost_loss):{rev_dis}")

    # ---------- Экспорт в CSV ----------
    print("\n=== Экспорт в data/raw/ ===")
    for t in ("dim_store", "dim_customer", "dim_reason", "dim_date",
              "dim_product", "fact_sales", "fact_supplies", "fact_disposals"):
        if t == "dim_product":
            # SCD2 — экспортируем только бизнес-колонки
            con.execute(f"""
                COPY (
                    SELECT product_id, product_name, category, brand
                    FROM dim_product WHERE is_current = TRUE
                ) TO '{RAW / 'dim_product.csv'}' (HEADER)
            """)
        else:
            con.execute(f"COPY (SELECT * FROM {t}) TO '{RAW / (t + '.csv')}' (HEADER)")
        print(f"  {t}.csv")

    con.close()
    print(f"\nOK → {db_path}")
    print(f"CSV в: {RAW}")


if __name__ == "__main__":
    main()