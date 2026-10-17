SELECT
    r.reason_name,
    sum(d.cost_loss) AS total_loss
FROM fact_disposals d
JOIN dim_reason r ON d.reason_id = r.reason_id
GROUP BY r.reason_name
ORDER BY total_loss DESC;