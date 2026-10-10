 Паспорт витрины (P02)

ФИО: Стефаненко, Езерский, Гарбуз · Дата: 2026-10-10 · Домен: розница (retail)

 1. Бизнес-цель витрины

Витрина показывает оборот розничной сети в разрезах регионов, магазинов,
категорий товаров и времени. Нужна для ответов на вопросы вида
«где и что продаётся лучше», «как меняется выручка по месяцам».

 2. Grain (одна фраза)

Одна строка факта = одна позиция в чеке: товар × количество × сумма
в конкретном магазине в конкретную дату.

 3. Fact-таблица(ы)

|    Имя     |                      Grain                   |    Примечание    |
|------------|----------------------------------------------|------------------|
| fact_sales | одна позиция в чеке (товар × магазин × дата) | sample: 15 строк |


 4. Меры

| Мера | Тип (sum ok / нет) | Определение |
|------|--------------------|-------------|
| amount         | sum ok    | сумма позиции в деньгах  |
| qty            | sum ok    | количество единиц товара |
| price_per_unit | sum НЕ ok | amount / qty — средняя цена, суммировать нельзя |
| check_size     | sum НЕ ok | сумма по чеку, требует агрегации по sale_id |


5. Измерения

| Dim | Ключ | Важные атрибуты | SCD1 / SCD2 / нет |
|-----|------|-----------------|-------------------|
| dim_store   | store_id   | store_name, city, region                        | SCD1 (затираем) |
| dim_product | product_id | product_name, category, brand                   | SCD2 (кандидат) |
| dim_date | date_id       | full_date, year, month, month_name, day_of_week | нет (статичный) |


6. Три бизнес-вопроса

1. Какой оборот (SUM(amount)) по регионам за январь 2024?
2. Топ-10 категорий товаров по обороту за весь период?
3. Как меняется средний чек по магазинам месяц к месяцу?


7. Эталонный SQL одной метрики (черновик → уточнить на P04)

```sql
-- Оборот по регионам за январь 2024
SELECT
    ds.region,
    SUM(fs.amount) AS revenue
FROM fact_sales fs
JOIN dim_store ds ON fs.store_id = ds.store_id
JOIN dim_date  dd ON fs.date_id  = dd.date_id
WHERE dd.year = 2024 AND dd.month = 1
GROUP BY ds.region
ORDER BY revenue DESC;
```


8. Риски / cut

- Кластер ClickHouse — не разворачиваем.
- Kafka / стриминг — batch-загрузка через init_ch.sh.
- ML-прогноз спроса — не обучаем.
- SCD2 для dim_store — пока SCD1.


9. Star-схема

```mermaid
erDiagram
    dim_store   ||--o{ fact_sales : store_id
    dim_product ||--o{ fact_sales : product_id
    dim_date    ||--o{ fact_sales : date_id

    dim_store {
        int store_id PK
        text store_name
        text city
        text region
    }
    dim_product {
        int product_id PK
        text product_name
        text category
        text brand
    }
    dim_date {
        int date_id PK
        date full_date
        int year
        int month
        text month_name
        int day_of_week
    }
    fact_sales {
        int sale_id PK
        int date_id FK
        int store_id FK
        int product_id FK
        int qty
        decimal amount
    }