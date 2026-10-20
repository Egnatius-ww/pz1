-- З07. DDL витрины retail_dw в ClickHouse (constellation: 3 факта + 5 измерений).

-- ============================================================
-- ИЗМЕРЕНИЯ
-- ============================================================

CREATE TABLE IF NOT EXISTS dim_store (
    store_id    Int32,
    store_name  String,
    city        String,
    region      String
)
ENGINE = MergeTree
ORDER BY (region, city, store_id);


CREATE TABLE IF NOT EXISTS dim_product (
    version_id    Int32,
    product_id    Int32,
    product_name  String,
    category      String,
    brand         String,
    valid_from    Date,
    valid_to      Nullable(Date),
    is_current    Bool
)
ENGINE = MergeTree
ORDER BY (product_id, valid_from);


CREATE TABLE IF NOT EXISTS dim_date (
    date_id      Int32,
    full_date    Date,
    year         Int32,
    month        Int32,
    month_name   String,
    day_of_week  Int32
)
ENGINE = MergeTree
ORDER BY (year, month, date_id);


CREATE TABLE IF NOT EXISTS dim_customer (
    customer_id    Int32,
    customer_name  String,
    city           String,
    loyalty_tier   String
)
ENGINE = MergeTree
ORDER BY (customer_id);


CREATE TABLE IF NOT EXISTS dim_reason (
    reason_id    Int32,
    reason_name  String
)
ENGINE = MergeTree
ORDER BY (reason_id);


-- ============================================================
-- ФАКТЫ
-- ============================================================

CREATE TABLE IF NOT EXISTS fact_sales (
    sale_id     Int64,
    date_id     Int32,
    store_id    Int32,
    product_id  Int32,
    customer_id Int32,
    qty         Int32,
    amount      Decimal(12,2)
)
ENGINE = MergeTree
ORDER BY (date_id, store_id, product_id, customer_id, sale_id);


CREATE TABLE IF NOT EXISTS fact_supplies (
    supply_id   Int64,
    date_id     Int32,
    store_id    Int32,
    product_id  Int32,
    qty         Int32,
    cost        Decimal(12,2)
)
ENGINE = MergeTree
ORDER BY (date_id, store_id, product_id, supply_id);


CREATE TABLE IF NOT EXISTS fact_disposals (
    disposal_id Int64,
    date_id     Int32,
    store_id    Int32,
    product_id  Int32,
    reason_id   Int32,
    qty         Int32,
    cost_loss   Decimal(12,2)
)
ENGINE = MergeTree
ORDER BY (date_id, store_id, product_id, reason_id, disposal_id);


-- ============================================================
-- MV для сводки
-- ============================================================
CREATE TABLE IF NOT EXISTS daily_store_revenue (
    full_date  Date,
    store_id   Int32,
    amount_sum Decimal(18,2)
)
ENGINE = SummingMergeTree
ORDER BY (full_date, store_id);

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_daily_store
TO daily_store_revenue
AS
SELECT
    dd.full_date           AS full_date,
    fs.store_id            AS store_id,
    sum(fs.amount)         AS amount_sum
FROM fact_sales fs
JOIN dim_date dd ON fs.date_id = dd.date_id
GROUP BY dd.full_date, fs.store_id;