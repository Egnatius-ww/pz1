-- Виджет 1: Эталон — оборот (Number)
-- Дашборд: "Розница 2024"
SELECT sum(amount) AS revenue
FROM fact_sales;