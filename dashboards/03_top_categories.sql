-- Виджет 3: Топ-10 категорий (Bar)
SELECT
    dp.category,
    sum(fs.amount) AS revenue
FROM fact_sales fs
JOIN dim_product dp ON fs.product_id = dp.product_id
GROUP BY dp.category
ORDER BY revenue DESC
LIMIT 10;