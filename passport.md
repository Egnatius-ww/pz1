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
| fact_sales | одна позиция в чеке (товар × магазин × дата) | sample: 2000000 |


 4. Меры

| Мера | Тип (sum ok / нет) | Определение |
|------|--------------------|-------------|
| amount         | sum ok    | сумма позиции в деньгах  |
| qty            | sum ok    | количество единиц товара |
| price_per_unit | sum НЕ ok | amount / qty — средняя цена, суммировать нельзя |
| check_size     | sum НЕ ok | сумма по чеку, требует агрегации по sale_id |


5. Измерения

| Dim         | Ключ       | Важные атрибуты               | SCD1 / SCD2 / нет |
|-----        |------      |-----------------              |-------------------|
| dim_store   | store_id   | store_name, city, region       | SCD1 (затираем) |
| dim_product | version_id (PK), product_id (business key) | product_name, category, brand, valid_from, valid_to, is_current | **SCD2** (реализовано) |
| dim_date    | date_id    | full_date, year, month, month_name, day_of_week                                                 | нет (статичный) |

 SCD2 для dim_product

Храним историю версий: при смене категории товара старая версия
закрывается (`valid_to`, `is_current = FALSE`), создаётся новая
(`valid_from`, `is_current = TRUE`).

Факт присоединяется к версии по дате события:
`fact_sales.date_id → dim_date.full_date BETWEEN dim_product.valid_from AND COALESCE(valid_to, '9999-12-31')`.




6. Три бизнес-вопроса

1. Какой оборот (SUM(amount)) по регионам за январь 2024?
2. Топ-10 категорий товаров по обороту за весь период?
3. Как меняется средний чек по магазинам месяц к месяцу?


7. Эталонный SQL одной метрики (черновик → уточнить на P04)

SELECT SUM(amount) AS revenue
FROM fact_sales;

**Эталонное число:** 78 220 000.00



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
        int version_id PK
        int product_id "business key"
        text product_name
        text category
        text brand
        date valid_from
        date valid_to
        bool is_current
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
        int product_id "business key"
        int qty
        decimal amount
    }