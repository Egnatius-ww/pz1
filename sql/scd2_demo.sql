-- P06. Демо SCD2 на dim_product
-- Товар 101 «Хлеб товар #0101»: в январе категория «Хлеб»,
-- с 2024-02-01 — «Выпечка».

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

-- 2a. Закрыть текущую версию товара 101
UPDATE dim_product
SET valid_to = DATE '2024-01-31',
    is_current = FALSE
WHERE product_id = 101 AND is_current = TRUE;

-- 2b. Вставить новую версию (взяв данные из только что закрытой)
INSERT INTO dim_product
    (version_id, product_id, product_name, category, brand,
     valid_from, valid_to, is_current)
SELECT
    (SELECT max(version_id) + 1 FROM dim_product),
    product_id,
    product_name,
    'Выпечка',
    brand,
    DATE '2024-02-01',
    NULL,
    TRUE
FROM dim_product
WHERE product_id = 101 AND valid_to = DATE '2024-01-31';   -- ← ищем закрытую версию


-- ============================================================
-- 3. ПОСЛЕ: две версии товара 101
-- ============================================================
SELECT version_id, product_id, product_name, category,
       valid_from, valid_to, is_current
FROM dim_product
WHERE product_id = 101
ORDER BY valid_from;


-- ============================================================
-- 4. Как факт присоединяется к версии по дате события:
--    январские продажи → "Хлеб", февральские → "Выпечка"
-- ============================================================
SELECT
    dp.category AS category_at_sale_date,
    count()     AS sales_count,
    sum(fs.amount) AS revenue,
    min(dd.full_date) AS first_sale,
    max(dd.full_date) AS last_sale
FROM fact_sales fs
JOIN dim_date    dd ON fs.date_id    = dd.date_id
JOIN dim_product dp ON fs.product_id = dp.product_id
                   AND dd.full_date BETWEEN dp.valid_from
                                        AND COALESCE(dp.valid_to, DATE '9999-12-31')
WHERE fs.product_id = 101
GROUP BY dp.category
ORDER BY first_sale;

-- ============================================================
-- 5. Тест: исторический срез (январь) не меняется после SCD2-обновления
-- Отчёт: оборот по категориям за январь 2024
-- -- Должен показать "Хлеб", а не "Выпечка"
-- ============================================================
SELECT
    dp.category AS category_at_sale_date,
    sum(fs.amount) AS revenue
FROM fact_sales fs
JOIN dim_date    dd ON fs.date_id    = dd.date_id
JOIN dim_product dp ON fs.product_id = dp.product_id
                   AND dd.full_date BETWEEN dp.valid_from
                                        AND COALESCE(dp.valid_to, DATE '9999-12-31')
WHERE dd.year = 2024 AND dd.month = 1
  AND dp.product_id = 101
GROUP BY dp.category;


-- ============================================================
-- 6. Контраст: тот же отчёт БЕЗ SCD2 (только текущая версия)
-- Врёт: январские продажи получат февральскую категорию
-- ============================================================
SELECT
    dp.category AS category_wrong,
    sum(fs.amount) AS revenue
FROM fact_sales fs
JOIN dim_date    dd ON fs.date_id    = dd.date_id
JOIN dim_product dp ON fs.product_id = dp.product_id
                   AND dp.is_current = TRUE
WHERE dd.year = 2024 AND dd.month = 1
  AND dp.product_id = 101
GROUP BY dp.category;