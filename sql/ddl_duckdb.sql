-- DDL витрины retail_dw в DuckDB
-- Соответствует паспорту (З02): constellation-схема (галактика)
-- 3 факта: fact_sales, fact_supplies, fact_disposals
-- 5 измерений: dim_store, dim_product, dim_date, dim_customer, dim_reason

-- ============================================================
-- ИЗМЕРЕНИЯ (DIMENSIONS)
-- ============================================================

-- Справочник: магазины (SCD1 — затираем старое)
CREATE TABLE IF NOT EXISTS dim_store (
    store_id    INTEGER PRIMARY KEY,
    store_name  VARCHAR NOT NULL,
    city        VARCHAR,
    region      VARCHAR
);

-- Справочник: товары (SCD2 — храним историю версий)
-- PK = version_id, а product_id — это business key (не уникален)
CREATE TABLE IF NOT EXISTS dim_product (
    version_id    INTEGER PRIMARY KEY,
    product_id    INTEGER NOT NULL,
    product_name  VARCHAR NOT NULL,
    category      VARCHAR,
    brand         VARCHAR,
    valid_from    DATE NOT NULL,
    valid_to      DATE,
    is_current    BOOLEAN NOT NULL DEFAULT TRUE
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

-- Справочник: покупатели (SCD1)
CREATE TABLE IF NOT EXISTS dim_customer (
    customer_id    INTEGER PRIMARY KEY,
    customer_name  VARCHAR NOT NULL,
    city           VARCHAR,
    loyalty_tier   VARCHAR  -- Bronze, Silver, Gold, Platinum
);

-- Справочник: причины списания (статичный)
CREATE TABLE IF NOT EXISTS dim_reason (
    reason_id    INTEGER PRIMARY KEY,
    reason_name  VARCHAR NOT NULL
);


-- ============================================================
-- ФАКТЫ (FACTS)
-- ============================================================

-- 1. Продажи (одна строка = позиция в чеке)
CREATE TABLE IF NOT EXISTS fact_sales (
    sale_id     BIGINT PRIMARY KEY,
    date_id     INTEGER NOT NULL REFERENCES dim_date(date_id),
    store_id    INTEGER NOT NULL REFERENCES dim_store(store_id),
    product_id  INTEGER NOT NULL,           -- business key, без FK (из-за SCD2)
    customer_id INTEGER NOT NULL REFERENCES dim_customer(customer_id),
    qty         INTEGER NOT NULL,
    amount      DECIMAL(12,2) NOT NULL
);

-- 2. Поставки / Привоз (одна строка = позиция поставки)
CREATE TABLE IF NOT EXISTS fact_supplies (
    supply_id   BIGINT PRIMARY KEY,
    date_id     INTEGER NOT NULL REFERENCES dim_date(date_id),
    store_id    INTEGER NOT NULL REFERENCES dim_store(store_id),
    product_id  INTEGER NOT NULL,           -- business key, без FK (из-за SCD2)
    qty         INTEGER NOT NULL,
    cost        DECIMAL(12,2) NOT NULL      -- закупочная стоимость
);

-- 3. Списания / Утилизация (одна строка = позиция списания)
CREATE TABLE IF NOT EXISTS fact_disposals (
    disposal_id BIGINT PRIMARY KEY,
    date_id     INTEGER NOT NULL REFERENCES dim_date(date_id),
    store_id    INTEGER NOT NULL REFERENCES dim_store(store_id),
    product_id  INTEGER NOT NULL,           -- business key, без FK (из-за SCD2)
    reason_id   INTEGER NOT NULL REFERENCES dim_reason(reason_id),
    qty         INTEGER NOT NULL,
    cost_loss   DECIMAL(12,2) NOT NULL      -- сумма потерь
);