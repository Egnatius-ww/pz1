SELECT
    c.customer_name,
    c.loyalty_tier,
    sum(s.amount) AS revenue
FROM fact_sales s
JOIN dim_customer c ON s.customer_id = c.customer_id
GROUP BY c.customer_name, c.loyalty_tier
ORDER BY revenue DESC
LIMIT 10;