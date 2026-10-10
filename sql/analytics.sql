-- З04. Аналитические запросы к витрине retail_dw (DuckDB)
-- Три ответа на три бизнес-вопроса из паспорта.

-- ============================================================
-- Вопрос 1: Какой оборот по регионам за январь 2024?
-- Тип: WHERE + GROUP BY
-- ============================================================
SELECT
    ds.region,
    SUM(fs.amount) AS revenue
FROM fact_sales fs
JOIN dim_store ds ON fs.store_id = ds.store_id
JOIN dim_date  dd ON fs.date_id  = dd.date_id
WHERE dd.year = 2024 AND dd.month = 1
GROUP BY ds.region
ORDER BY revenue DESC;


-- ============================================================
-- Вопрос 2: Топ-10 категорий товаров по обороту за весь период
-- Тип: GROUP BY + ORDER BY + LIMIT
-- ============================================================
SELECT
    dp.category,
    SUM(fs.amount) AS revenue
FROM fact_sales fs
JOIN dim_product dp ON fs.product_id = dp.product_id
GROUP BY dp.category
ORDER BY revenue DESC
LIMIT 10;


-- ============================================================
-- Вопрос 3: Как меняется средний чек по магазинам месяц к месяцу?
-- Тип: CTE + GROUP BY + ОКОННАЯ ФУНКЦИЯ (RANK() OVER)
-- ============================================================
WITH checks AS (
    SELECT
        fs.sale_id,
        fs.store_id,
        dd.year,
        dd.month,
        SUM(fs.amount) AS check_size
    FROM fact_sales fs
    JOIN dim_date dd ON fs.date_id = dd.date_id
    GROUP BY fs.sale_id, fs.store_id, dd.year, dd.month
),
monthly AS (
    SELECT
        year,
        month,
        store_id,
        AVG(check_size) AS avg_check
    FROM checks
    GROUP BY year, month, store_id
)
SELECT
    m.year,
    m.month,
    ds.store_name,
    m.avg_check,
    RANK() OVER (PARTITION BY m.year, m.month ORDER BY m.avg_check DESC) AS rank_in_month
FROM monthly m
JOIN dim_store ds ON m.store_id = ds.store_id
ORDER BY m.year, m.month, rank_in_month;