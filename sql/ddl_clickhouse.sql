-- З07. DDL витрины retail_dw в ClickHouse (MergeTree).

-- ============================================================
-- Справочник: магазины
-- ============================================================
CREATE TABLE IF NOT EXISTS dim_store (
    store_id    Int32,
    store_name  String,
    city        String,
    region      String
)
ENGINE = MergeTree
ORDER BY (region, city, store_id);


-- ============================================================
-- Справочник: товары (SCD2 — с версиями)
-- ============================================================
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


-- ============================================================
-- Справочник: календарь
-- ============================================================
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


-- ============================================================
-- Факт: продажи
-- Деньги — Decimal, НЕ Float (иначе сверка с BI разъедется)
-- ============================================================
CREATE TABLE IF NOT EXISTS fact_sales (
    sale_id     Int32,
    date_id     Int32,
    store_id    Int32,
    product_id  Int32,
    qty         Int32,
    amount      Decimal(12,2)
)
ENGINE = MergeTree
ORDER BY (date_id, store_id, product_id, sale_id);