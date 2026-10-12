"""З09. Сверка сводки с детальной."""
import clickhouse_connect

client = clickhouse_connect.get_client(
    host="localhost", port=8123,
    username="default", password="",
    database="retail_dw",
)

print("=== Сверка сводки с детальной ===\n")

detailed = client.command("SELECT sum(amount) FROM fact_sales")
aggregate = client.command("SELECT sum(amount_sum) FROM daily_store_revenue")

print(f"fact_sales.sum(amount):              {detailed}")
print(f"daily_store_revenue.sum(amount_sum): {aggregate}")

d_str = str(detailed).rstrip("0").rstrip(".")
a_str = str(aggregate).rstrip("0").rstrip(".")
ok = d_str == a_str
print(f"\n{'✓ Совпадают' if ok else '❌ РАСХОЖДЕНИЕ'}")

print("\n=== Сводка ===")
res = client.query("SELECT * FROM daily_store_revenue ORDER BY full_date, store_id")
print(" | ".join(res.column_names))
for row in res.result_rows:
    print(" | ".join(str(v) for v in row))

client.close()