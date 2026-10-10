# Проект: Розничные продажи (pz1)

ФИО: Стефанеко, Езерский, Гарбуз
Группа: ПИ-232
Домен: розница (retail)

## Стенд
ClickHouse + Metabase из папки `E:\olap\Стенд`:
    cd /e/olap/Стенд
    docker compose up -d
    ./scripts/init_ch.sh

Порты:
- ClickHouse HTTP: 8123
- ClickHouse native: 9000
- Metabase: 3000

## Сырьё (`data/raw/`, star schema)

### dim_store.csv — магазины
- store_id    — int, PK
- store_name  — text, название
- city        — text, город
- region      — text, регион

### dim_product.csv — товары
- product_id   — int, PK
- product_name — text, название
- category     — text, категория
- brand        — text, бренд

### dim_date.csv — календарь
- date_id     — int, PK (YYYYMMDD)
- full_date   — date
- year        — int
- month       — int
- month_name  — text
- day_of_week — int

### fact_sales.csv — продажи
- sale_id    — int, PK
- date_id    — int, FK → dim_date
- store_id   — int, FK → dim_store
- product_id — int, FK → dim_product
- qty        — int, количество
- amount     — decimal, сумма

## Что считаю
Метрика: выручка по регионам и категориям.
Вопросы:
1. Топ категорий по выручке.
2. Динамика продаж по месяцам.
3. Средний чек по магазинам.

## Загрузка данных в DuckDB (З03)

Требования: Python 3.10+, пакет `duckdb`.

```bash
py -m pip install duckdb
py scripts/load_duckdb.py