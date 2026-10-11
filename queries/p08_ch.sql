-- З08. Те же 5 запросов из P04, но для ClickHouse.
-- Отличия от DuckDB: GROUPING SETS → WITH ROLLUP; функции строчными.

-- ============================================================
-- 1. SLICE: оборот за период (январь 2024)
-- ============================================================
SELECT
    dd.year,
    dd.month,
    sum(fs.amount) AS revenue
FROM fact_sales fs
JOIN dim_date dd ON fs.date_id = dd.date_id
WHERE dd.year = 2024 AND dd.month = 1
GROUP BY dd.year, dd.month;


-- ============================================================
-- 2. ROLL-UP: оборот по месяцам и по годам
-- В CH GROUPING SETS неудобен → WITH ROLLUP даёт то же:
-- (year, month), (year), ()
-- ============================================================
SELECT
    dd.year,
    dd.month,
    sum(fs.amount) AS revenue
FROM fact_sales fs
JOIN dim_date dd ON fs.date_id = dd.date_id
GROUP BY dd.year, dd.month WITH ROLLUP
ORDER BY dd.year ASC NULLS LAST, dd.month ASC NULLS LAST;


-- ============================================================
-- 3. DICE: оборот по региону + категории
-- ============================================================
SELECT
    ds.region,
    dp.category,
    sum(fs.amount) AS revenue
FROM fact_sales fs
JOIN dim_store   ds ON fs.store_id   = ds.store_id
JOIN dim_product dp ON fs.product_id = dp.product_id
GROUP BY ds.region, dp.category
ORDER BY ds.region, revenue DESC;


-- ============================================================
-- 4. ОКНО: доля категории в обороте + место в рейтинге
-- ============================================================
WITH cat_rev AS (
    SELECT
        dp.category,
        sum(fs.amount) AS revenue
    FROM fact_sales fs
    JOIN dim_product dp ON fs.product_id = dp.product_id
    GROUP BY dp.category
)
SELECT
    category,
    revenue,
    round(revenue * 100.0 / sum(revenue) OVER (), 2) AS share_pct,
    RANK() OVER (ORDER BY revenue DESC) AS rank
FROM cat_rev
ORDER BY rank;


-- ============================================================
-- 5. ТОП-N: топ-3 магазина по обороту
-- ============================================================
SELECT
    ds.store_name,
    ds.city,
    sum(fs.amount) AS revenue
FROM fact_sales fs
JOIN dim_store ds ON fs.store_id = ds.store_id
GROUP BY ds.store_name, ds.city
ORDER BY revenue DESC
LIMIT 3;


-- ============================================================
-- 6. ЭТАЛОН: главная метрика (sum amount)
-- ============================================================
SELECT sum(amount) AS revenue
FROM fact_sales;