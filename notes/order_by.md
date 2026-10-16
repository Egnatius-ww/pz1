# Обоснование ORDER BY в ClickHouse

`ORDER BY` в MergeTree — **не PRIMARY KEY**, а порядок хранения строк
на диске. Дубли не запрещаются; идемпотентность — через `TRUNCATE`
перед загрузкой (см. `etl/load_ch.py`).

## fact_sales
ORDER BY (date_id, store_id, product_id, sale_id)

Порядок отражает разрезы из паспорта:
- **date_id первым** — большинство запросов фильтруют период («за январь»).
- **store_id вторым** — оборот по регионам/магазинам (JOIN с dim_store).
- **product_id третьим** — топ категорий (JOIN с dim_product).
- **sale_id последним** — стабильный порядок внутри дня.

## dim_product
ORDER BY (product_id, valid_from)

SCD2: у товара несколько версий. Сортировка по product_id + valid_from —
запрос «все версии товара X» читает соседние строки.

## dim_store
ORDER BY (region, city, store_id)

Основной разрез — регион. Ускоряет «оборот по регионам» и «по городам».

## dim_date
ORDER BY (year, month, date_id)

Основной разрез — год/месяц. Ускоряет фильтры «за январь», «за 2024».

## ORDER BY ≠ PARTITION BY

Это **разные рычаги**:
- **ORDER BY** — порядок **внутри** куска. Помогает пропускать строки.
- **PARTITION BY** — разбиение **на куски** (файлы). Помогает читать/удалять период.

В `fact_sales` партиции **нет**: 2 млн строк — один кусок, `ORDER BY` достаточен.
При росте до **100M+** — `PARTITION BY intDiv(date_id, 100)` (по месяцу).