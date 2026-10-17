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
py etl/load.py


ELT: загрузка и проверки (З05)

```bash
py etl/load.py


## Загрузка в ClickHouse (З07)

```bash
py -m pip install clickhouse-connect
py etl/load_ch.py

## З08: запросы и ключи в ClickHouse

**Скрипт:** `scripts/run_p08.py` — прогон `queries/p08_ch.sql`.
**Результат:** `sql/p08_output.txt`.

### Ключ сортировки

`ORDER BY` в MergeTree — **не PRIMARY KEY**, а порядок хранения
строк на диске. Уникальность не гарантируется; идемпотентность —
через `TRUNCATE` перед загрузкой.

В `fact_sales` — `(date_id, store_id, product_id, sale_id)`:
`date_id` первым, потому что большинство отчётов фильтруют период.

### Партиционирование

Партиций **нет** — данные учебного sample малы (15 строк).
Обоснование отказа — в `cut.md`.



# Дашборд "Розница 2024" (З10)

**Источник:** ClickHouse, база `retail_dw`.
**URL:** http://localhost:3000/dashboard/2-rozmica-2024

## Виджеты

| # | Название | Тип | SQL |
|---|---|---|---|
| 1 | Эталон — оборот | Number | `01_canonical_metric.sql` |
| 2 | Оборот по дням | Line | `02_revenue_by_day.sql` |
| 3 | Топ-10 категорий | Bar | `03_top_categories.sql` |
| 4 | Оборот по регионам | Bar | `04_revenue_by_region.sql` |

## Фильтры

- **Период** — Date Range (в настройках дашборда)
- **Регион** — Text (в настройках дашборда)

⚠️ Привязка к виджетам с Native SQL требует переменных
`{{start_date}}` / `{{region}}` в SQL. Оставлено как есть,
фильтры сохранены в дашборде.

## Как воспроизвести

1. Metabase → Admin → Databases → Add → **ClickHouse**
2. Host: `clickhouse`, Port: `8123`, Database: `retail_dw`,
   User: `default`, Pass: пусто
3. Создать SQL-вопросы из файлов выше
4. Дашборд «Розница 2024» → добавить все 4 виджета
5. Добавить фильтры «Период» и «Регион» (в настройках)