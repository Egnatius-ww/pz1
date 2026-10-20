# З11. Сверка SQL и карточки Metabase

## Условия сверки

- **Период:** весь 2024 год (без фильтров)
- **Регион:** все
- **Магазин:** все
- **Фильтры дашборда:** не применяются

## Формула метрики

`SUM(amount) FROM fact_sales` — оборот, без фильтров.

Формула зафиксирована в файле: **`sql/canonical_metric.sql`**.

## Числа

| Источник | Что смотрим | Значение |
|---|---|---|
| SQL в ClickHouse | `SELECT sum(amount) FROM retail_dw.fact_sales` | **78 220 000** |
| Metabase | Карточка «Эталон — оборот» (дашборд «Розница 2024») | **78 220 000** |

## Вывод

**Числа совпадают.** Расхождений нет.

**Причина:** источник данных один — ClickHouse, база `retail_dw`. Формула метрики одинаковая (`SUM(amount)` без фильтров и группировок). Карточка Metabase смотрит в ту же таблицу `fact_sales` тем же запросом, что и `canonical_metric.sql`.

## Команды для воспроизведения

**1. SQL (ClickHouse):**
```bash
docker exec olap_clickhouse clickhouse-client --query "SELECT sum(amount) FROM retail_dw.fact_sales"
# → 78220000