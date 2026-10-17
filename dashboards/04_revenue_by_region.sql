-- Виджет 4: Оборот по регионам (Bar)
SELECT
    ds.region,
    sum(fs.amount) AS revenue
FROM fact_sales fs
JOIN dim_store ds ON fs.store_id = ds.store_id
GROUP BY ds.region
ORDER BY revenue DESC;