-- P04. Аналитический SQL — 5 обязательных типов запросов
-- Витрина: retail_dw (DuckDB)

-- ============================================================
-- 1. SLICE: оборот за период (январь 2024)
-- Обрезаем факт по одному разрезу — время.
-- ============================================================
SELECT
    dd.year,
    dd.month,
    SUM(fs.amount) AS revenue
FROM fact_sales fs
JOIN dim_date dd ON fs.date_id = dd.date_id
WHERE dd.year = 2024 AND dd.month = 1
GROUP BY dd.year, dd.month;


-- ============================================================
-- 2. ROLL-UP: оборот по месяцам и по годам
-- Свёртка снизу вверх: детализация месяц → год.
-- GROUPING SETS даёт и месяц, и год, и общий итог в одном запросе.
-- ============================================================
SELECT
    dd.year,
    dd.month,
    SUM(fs.amount) AS revenue
FROM fact_sales fs
JOIN dim_date dd ON fs.date_id = dd.date_id
GROUP BY GROUPING SETS (
    (dd.year, dd.month),
    (dd.year),
    ()
)
ORDER BY dd.year NULLS LAST, dd.month NULLS LAST;


-- ============================================================
-- 3. DICE: оборот по региону + категории
-- Срез по двум разрезам одновременно.
-- ============================================================
SELECT
    ds.region,
    dp.category,
    SUM(fs.amount) AS revenue
FROM fact_sales fs
JOIN dim_store   ds ON fs.store_id   = ds.store_id
JOIN dim_product dp ON fs.product_id = dp.product_id
GROUP BY ds.region, dp.category
ORDER BY ds.region, revenue DESC;


-- ============================================================
-- 4. ОКНО: доля категории в обороте + место в рейтинге
-- SUM() OVER () — доля, RANK() OVER — место.
-- ============================================================
WITH cat_rev AS (
    SELECT
        dp.category,
        SUM(fs.amount) AS revenue
    FROM fact_sales fs
    JOIN dim_product dp ON fs.product_id = dp.product_id
    GROUP BY dp.category
)
SELECT
    category,
    revenue,
    ROUND(revenue * 100.0 / SUM(revenue) OVER (), 2) AS share_pct,
    RANK() OVER (ORDER BY revenue DESC) AS rank
FROM cat_rev
ORDER BY rank;


-- ============================================================
-- 5. ТОП-N: топ-3 магазина по обороту
-- ============================================================
SELECT
    ds.store_name,
    ds.city,
    SUM(fs.amount) AS revenue
FROM fact_sales fs
JOIN dim_store ds ON fs.store_id = ds.store_id
GROUP BY ds.store_name, ds.city
ORDER BY revenue DESC
LIMIT 3;