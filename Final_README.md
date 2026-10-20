# Проект: Витрина розничной сети (Constellation)

**Студенты:** Стефаненко, Езерский, Гарбуз
**Группа:** ПИ-232
**Домен:** розница (retail)
**Архитектура:** Constellation (3 факта, 5 измерений)

---

## Быстрый старт (5 шагов)

### 1. Поднять Docker и ClickHouse
```bash
cd E:\olap\Стенд
docker compose up -d
curl.exe http://localhost:8123/ping   # Должно быть "Ok."