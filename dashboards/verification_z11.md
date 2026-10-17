# З11. Сверка SQL и карточки Metabase

## Условия сверки

- **Период:** весь 2024 год (без фильтров)
- **Регион:** все
- **Фильтры дашборда:** не применяются

## Формула метрики

`SUM(amount) FROM fact_sales` — оборот, без фильтров.

Живёт в: **`sql/canonical_metric.sql`**.

## Числа

| Источник | Что | Значение |
|---|---|---|
| SQL в ClickHouse | `SELECT sum(amount) FROM retail_dw.fact_sales` | **78 220 000** |
| Metabase | Карточка «Эталон — оборот» на дашборде «Розница 2024» | **78 220 000** |

## Вывод

**Числа совпадают.** Расхождений нет.

Причина — источник данных один: **ClickHouse**, база `retail_dw`.
Формула метрики одинаковая: `SUM(amount)` без фильтров и группировок.

## Команды для воспроизведения

**1. SQL (ClickHouse):**

```bash
docker exec olap_clickhouse clickhouse-client --query "SELECT sum(amount) FROM retail_dw.fact_sales"
# → 78220000