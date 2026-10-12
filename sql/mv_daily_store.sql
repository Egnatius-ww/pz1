-- Целевая таблица
CREATE TABLE IF NOT EXISTS daily_store_revenue (
    full_date  Date,
    store_id   Int32,
    amount_sum Decimal(18,2)
)
ENGINE = SummingMergeTree
ORDER BY (full_date, store_id);

-- Materialized View
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_daily_store
TO daily_store_revenue
AS
SELECT
    dd.full_date,
    fs.store_id,
    sum(fs.amount) AS amount_sum
FROM fact_sales fs
JOIN dim_date dd ON fs.date_id = dd.date_id
GROUP BY dd.full_date, fs.store_id;