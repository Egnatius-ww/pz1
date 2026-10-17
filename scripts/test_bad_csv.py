"""
З05. Тест: сломать amount в fact_sales.csv, запустить etl/load.py,
показать, что проверка стопорит загрузку, восстановить из бэкапа.
Безопасно: try/finally гарантирует восстановление.

Запуск: py scripts/test_bad_csv.py
"""
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CSV = ROOT / "data" / "raw" / "fact_sales.csv"
BAK = ROOT / "data" / "raw" / "fact_sales.csv.bak"

def main():
    if not CSV.exists():
        print(f"❌ Файл {CSV} не найден. Сначала сгенерируй данные.")
        sys.exit(1)

    # 1. Бэкап
    if BAK.exists():
        BAK.unlink()
    shutil.copy(CSV, BAK)
    print(f"✓ Бэкап: {BAK}")

    try:
        # 2. Сломать: заменить amount в первой строке данных на -100
        with open(CSV, encoding="utf-8") as f:
            lines = f.readlines()

        # fact_sales.csv: sale_id,date_id,store_id,product_id,customer_id,qty,amount
        parts = lines[1].strip().split(",")
        old_amount = parts[-1]
        parts[-1] = "-100"
        lines[1] = ",".join(parts) + "\n"

        with open(CSV, "w", encoding="utf-8", newline="") as f:
            f.writelines(lines)

        print(f"✓ Сломано: amount {old_amount} → -100")
        print("\n--- CSV (первые 3 строки) ---")
        with open(CSV, encoding="utf-8") as f:
            for _ in range(3):
                print(" ", f.readline().rstrip())

        # 3. Запустить load.py — должен УПАСТЬ
        print("\n--- py etl/load.py ---")
        result = subprocess.run(
            [sys.executable, "etl/load.py"],
            capture_output=True, text=True, cwd=ROOT
        )
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        print(f"exit code: {result.returncode}")

        # 4. Проверка
        if result.returncode == 1 and "ЗАГРУЗКА ОСТАНОВЛЕНА" in result.stdout:
            print("\n✅ ПРОВЕРКА РАБОТАЕТ: load остановлен с кодом 1")
        else:
            print("\n⚠️ Неожиданно: load не остановился или не тот код")

    finally:
        # 5. Восстановить
        shutil.move(str(BAK), str(CSV))
        print(f"\n✓ Восстановлено из бэкапа")
        print("\n--- CSV (первые 3 строки) ---")
        with open(CSV, encoding="utf-8") as f:
            for _ in range(3):
                print(" ", f.readline().rstrip())

        # 6. Убедиться, что снова работает
        print("\n--- py etl/load.py (должно быть OK) ---")
        result = subprocess.run(
            [sys.executable, "etl/load.py"],
            capture_output=True, text=True, cwd=ROOT
        )
        # печатаем только конец вывода, чтобы не заспамить
        print(result.stdout[-700:])
        print(f"exit code: {result.returncode}")

if __name__ == "__main__":
    main()