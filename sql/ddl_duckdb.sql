-- DDL витрины retail_dw в DuckDB
-- Соответствует паспорту (З02): star-схема, fact_sales + 3 dim
-- Grain: одна строка fact_sales = одна позиция в чеке
--        (товар × количество × сумма, в магазине, в дату)
-- Справочник: магазины (SCD1 — затираем)
CREATE TABLE IF NOT EXISTS dim_store (
    store_id    INTEGER PRIMARY KEY,
    store_name  VARCHAR NOT NULL,
    city        VARCHAR,
    region      VARCHAR
);

-- Справочник: товары (SCD2 — кандидат)
CREATE TABLE IF NOT EXISTS dim_product (
    product_id    INTEGER PRIMARY KEY,
    product_name  VARCHAR NOT NULL,
    category      VARCHAR,
    brand         VARCHAR
);

-- Справочник: календарь (статичный)
CREATE TABLE IF NOT EXISTS dim_date (
    date_id      INTEGER PRIMARY KEY,
    full_date    DATE NOT NULL,
    year         INTEGER,
    month        INTEGER,
    month_name   VARCHAR,
    day_of_week  INTEGER
);

-- Факт: одна строка = одна позиция в чеке
CREATE TABLE IF NOT EXISTS fact_sales (
    sale_id     INTEGER PRIMARY KEY,
    date_id     INTEGER NOT NULL REFERENCES dim_date(date_id),
    store_id    INTEGER NOT NULL REFERENCES dim_store(store_id),
    product_id  INTEGER NOT NULL REFERENCES dim_product(product_id),
    qty         INTEGER NOT NULL,
    amount      DECIMAL(12,2) NOT NULL   -- деньги — DECIMAL, не FLOAT
);