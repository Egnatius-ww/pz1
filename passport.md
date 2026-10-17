# Паспорт витрины (P02 / зачёт)

ФИО: Стефаненко, Езерский, Гарбуз · Дата: 2026-10-17 · Домен: розница (retail)

## 1. Бизнес-цель витрины

Витрина показывает **полный цикл движения товара** в розничной сети:
привоз (поставки), продажи и списания (утилизацию). Нужна для ответов
на вопросы «сколько продали», «сколько завезли», «сколько списали
и почему», «какой процент потерь».

## 2. Grain — одна строка каждого факта

- **fact_sales**: одна строка = одна позиция в чеке (товар × количество × сумма) в конкретном магазине в конкретную дату.
- **fact_supplies**: одна строка = одна позиция поставки (товар × количество) в конкретный магазин в конкретную дату.
- **fact_disposals**: одна строка = одна позиция списания (товар × количество × причина) в конкретном магазине в конкретную дату.

⚠️ **Не путать:** три разных grain, три разных факта. У каждого — своя семантика.

## 3. Fact-таблицы

| Имя | Grain | Примечание |
|---|---|---|
| fact_sales | позиция в чеке (товар × магазин × дата) | 2 000 000 строк |
| fact_supplies | позиция поставки (товар × магазин × дата) | 200 000 строк |
| fact_disposals | позиция списания (товар × магазин × дата × причина) | 50 000 строк |

## 4. Меры

| Мера | Fact | Тип (sum ok / нет) | Определение |
|---|---|---|---|
| amount | fact_sales | sum ok | сумма позиции в деньгах |
| qty | fact_sales | sum ok | количество проданных единиц |
| price_per_unit | fact_sales | sum НЕ ok | amount / qty — средняя цена, суммировать нельзя |
| check_size | fact_sales | sum НЕ ok | сумма по чеку, требует агрегации по sale_id |
| qty | fact_supplies | sum ok | количество привезённых единиц |
| cost | fact_supplies | sum ok | себестоимость поставки |
| qty | fact_disposals | sum ok | количество списанных единиц |
| cost_loss | fact_disposals | sum ok | сумма потерь от списания |

## 5. Измерения

| Dim | Ключ | Важные атрибуты | SCD1 / SCD2 / нет |
|---|---|---|---|
| dim_store | store_id | store_name, city, region | SCD1 |
| dim_product | version_id (PK), product_id (business key) | product_name, category, brand, valid_from, valid_to, is_current | **SCD2** (реализовано) |
| dim_date | date_id | full_date, year, month, month_name, day_of_week | нет (статичный) |
| dim_reason | reason_id | reason_name | нет (статичный) |
| dim_customer | customer_id | customer_name, city, loyalty_tier | SCD1 |

### SCD2 для dim_product

Храним историю версий: при смене категории товара старая версия
закрывается (`valid_to`, `is_current = FALSE`), создаётся новая
(`valid_from`, `is_current = TRUE`).

Факт присоединяется к версии по дате события:
`fact_sales.date_id → dim_date.full_date BETWEEN dim_product.valid_from AND COALESCE(valid_to, '9999-12-31')`.

## 6. Бизнес-вопросы

1. Какой оборот (`SUM(amount)`) по регионам за январь 2024?
2. Топ-10 категорий товаров по обороту за весь период?
3. Как меняется средний чек по магазинам месяц к месяцу?
4. Какая доля списаний от объёма привоза по категориям (shrinkage rate)?
5. Какие причины списаний самые частые?
6. Кто наши топ-10 клиентов по выручке за 2024 год?

## 7. Эталонный SQL одной метрики

```sql
SELECT SUM(amount) AS revenue
FROM fact_sales;

**Эталонное число:** 78 220 000.00



8. Риски / cut
Кластер ClickHouse — не разворачиваем.

Kafka / стриминг — batch-загрузка через load_ch.py.

ML-прогноз спроса — не обучаем.

SCD2 для dim_store — пока SCD1.

Остатки на складе — не храним, только движения (приход/расход).


9. Star-схема

```mermaid
erDiagram
    dim_store   ||--o{ fact_sales    : store_id
    dim_store   ||--o{ fact_supplies : store_id
    dim_store   ||--o{ fact_disposals : store_id
    dim_product ||--o{ fact_sales    : product_id
    dim_product ||--o{ fact_supplies : product_id
    dim_product ||--o{ fact_disposals : product_id
    dim_date    ||--o{ fact_sales    : date_id
    dim_date    ||--o{ fact_supplies : date_id
    dim_date    ||--o{ fact_disposals : date_id
    dim_reason  ||--o{ fact_disposals : reason_id
    dim_customer ||--o{ fact_sales : customer_id

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
    dim_reason {
        int reason_id PK
        text reason_name
    }
    dim_customer {
        int customer_id PK
        text customer_name
        text city
        text loyalty_tier
    }
    fact_sales {
        int sale_id PK
        int date_id FK
        int store_id FK
        int product_id "business key"
        int customer_id FK
        int qty
        decimal amount
    }
    fact_supplies {
        int supply_id PK
        int date_id FK
        int store_id FK
        int product_id "business key"
        int qty
        decimal cost
    }
    fact_disposals {
        int disposal_id PK
        int date_id FK
        int store_id FK
        int product_id "business key"
        int reason_id FK
        int qty
        decimal cost_loss
    }