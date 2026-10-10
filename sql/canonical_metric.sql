-- З04. Эталон главной метрики: оборот (SUM(amount)).
-- Это число должно совпасть с карточкой дашборда в З11.
SELECT SUM(amount) AS revenue
FROM fact_sales;