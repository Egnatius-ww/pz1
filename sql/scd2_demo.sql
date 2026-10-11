-- P06. Демо SCD2 на dim_product
-- Товар 101 «Молоко 1л»: в январе категория «Молочка»,
-- с 2024-02-01 — «Молочные продукты».

-- ============================================================
-- 1. ДО: одна версия товара 101
-- ============================================================
SELECT version_id, product_id, product_name, category,
       valid_from, valid_to, is_current
FROM dim_product
WHERE product_id = 101
ORDER BY valid_from;


-- ============================================================
-- 2. Смена атрибута: закрываем старую версию, добавляем новую
-- ============================================================
UPDATE dim_product
SET valid_to = DATE '2024-01-31',
    is_current = FALSE
WHERE product_id = 101 AND is_current = TRUE;

INSERT INTO dim_product
    (version_id, product_id, product_name, category, brand,
     valid_from, valid_to, is_current)
SELECT
    (SELECT max(version_id) + 1 FROM dim_product),
    product_id,
    product_name,
    'Молочные продукты',
    brand,
    DATE '2024-02-01',
    NULL,
    TRUE
FROM dim_product
WHERE product_id = 101 AND version_id = 1;


-- ============================================================
-- 3. ПОСЛЕ: две версии товара 101
-- ============================================================
SELECT version_id, product_id, product_name, category,
       valid_from, valid_to, is_current
FROM dim_product
WHERE product_id = 101
ORDER BY valid_from;


-- ============================================================
-- 4. Как факт присоединяется к версии по дате события
-- ============================================================
SELECT
    fs.sale_id,
    dd.full_date,
    fs.product_id,
    dp.category AS category_at_sale_date,
    dp.valid_from,
    dp.valid_to
FROM fact_sales fs
JOIN dim_date    dd ON fs.date_id    = dd.date_id
JOIN dim_product dp ON fs.product_id = dp.product_id
                   AND dd.full_date BETWEEN dp.valid_from
                                        AND COALESCE(dp.valid_to, DATE '9999-12-31')
WHERE fs.product_id = 101
ORDER BY dd.full_date;