-- З08. 9 запросов из P04, адаптированных под ClickHouse.
-- Отличия: GROUPING SETS → WITH ROLLUP; функции строчными.

-- ============================================================
-- 1. SLICE
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
-- 2. ROLL-UP
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
-- 3. DICE
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
-- 4. ОКНО
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
-- 5. ТОП-N
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
-- 6. SHRINKAGE
-- ============================================================
WITH supplies AS (
    SELECT dp.category, sum(s.cost) AS supply_cost
    FROM fact_supplies s
    JOIN dim_product dp ON s.product_id = dp.product_id
    GROUP BY dp.category
),
disposals AS (
    SELECT dp.category, sum(d.cost_loss) AS disposal_cost
    FROM fact_disposals d
    JOIN dim_product dp ON d.product_id = dp.product_id
    GROUP BY dp.category
)
SELECT
    s.category,
    s.supply_cost,
    d.disposal_cost,
    round(d.disposal_cost * 100.0 / s.supply_cost, 2) AS shrinkage_pct
FROM supplies s
LEFT JOIN disposals d ON s.category = d.category
ORDER BY shrinkage_pct DESC;


-- ============================================================
-- 7. ТОП ПРИЧИН СПИСАНИЙ
-- ============================================================
SELECT
    r.reason_name,
    sum(d.cost_loss) AS total_loss,
    count() AS disposal_count
FROM fact_disposals d
JOIN dim_reason r ON d.reason_id = r.reason_id
GROUP BY r.reason_name
ORDER BY total_loss DESC;


-- ============================================================
-- 8. ТОП-10 КЛИЕНТОВ
-- ============================================================
SELECT
    c.customer_name,
    c.loyalty_tier,
    sum(s.amount) AS revenue
FROM fact_sales s
JOIN dim_customer c ON s.customer_id = c.customer_id
GROUP BY c.customer_name, c.loyalty_tier
ORDER BY revenue DESC
LIMIT 10;


-- ============================================================
-- 9. ЭТАЛОН
-- ============================================================
SELECT sum(amount) AS revenue FROM fact_sales;