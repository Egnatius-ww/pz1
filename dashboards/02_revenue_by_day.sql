-- Виджет 2: Оборот по дням (Line)
-- Источник: MV daily_store_revenue
SELECT
    full_date,
    sum(amount_sum) AS revenue
FROM daily_store_revenue
GROUP BY full_date
ORDER BY full_date;