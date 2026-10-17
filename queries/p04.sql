-- P04. Аналитический SQL — 8 запросов (5 базовых + 3 новых по constellation)
-- Витрина: retail_dw (DuckDB)

-- ============================================================
-- 1. SLICE: оборот за январь 2024
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
-- 2. ROLL-UP: оборот по месяцам и годам
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


-- ============================================================
-- 6. SHRINKAGE: доля списаний от объёма привоза по категориям
-- ============================================================
WITH supplies AS (
    SELECT dp.category, SUM(s.cost) AS supply_cost
    FROM fact_supplies s
    JOIN dim_product dp ON s.product_id = dp.product_id
    GROUP BY dp.category
),
disposals AS (
    SELECT dp.category, SUM(d.cost_loss) AS disposal_cost
    FROM fact_disposals d
    JOIN dim_product dp ON d.product_id = dp.product_id
    GROUP BY dp.category
)
SELECT
    s.category,
    s.supply_cost,
    d.disposal_cost,
    ROUND(d.disposal_cost * 100.0 / s.supply_cost, 2) AS shrinkage_pct
FROM supplies s
LEFT JOIN disposals d ON s.category = d.category
ORDER BY shrinkage_pct DESC;


-- ============================================================
-- 7. ТОП ПРИЧИН СПИСАНИЙ
-- ============================================================
SELECT
    r.reason_name,
    SUM(d.cost_loss) AS total_loss,
    COUNT(*) AS disposal_count
FROM fact_disposals d
JOIN dim_reason r ON d.reason_id = r.reason_id
GROUP BY r.reason_name
ORDER BY total_loss DESC;


-- ============================================================
-- 8. ТОП-10 КЛИЕНТОВ ПО ВЫРУЧКЕ
-- ============================================================
SELECT
    c.customer_name,
    c.loyalty_tier,
    SUM(s.amount) AS revenue
FROM fact_sales s
JOIN dim_customer c ON s.customer_id = c.customer_id
GROUP BY c.customer_name, c.loyalty_tier
ORDER BY revenue DESC
LIMIT 10;


-- ============================================================
-- 9. ЭТАЛОН: главная метрика
-- ============================================================
SELECT SUM(amount) AS revenue FROM fact_sales;