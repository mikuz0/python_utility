#!/usr/bin/env python3
import subprocess

def test_status():
    print("=== Проверка статуса Yandex.Disk ===\n")
    
    # Проверяем процесс
    result = subprocess.run(["ps", "aux"], capture_output=True, text=True)
    found = False
    for line in result.stdout.split('\n'):
        if 'yandex-disk' in line and 'grep' not in line:
            print(f"Процесс найден: {line.strip()}")
            found = True
    
    if not found:
        print("Процесс yandex-disk не найден")
    
    print("\n=== Вывод yandex-disk status ===\n")
    result = subprocess.run(["yandex-disk", "status"], capture_output=True, text=True)
    print(result.stdout)
    
    print("\n=== Анализ статуса ===\n")
    if "Статус ядра синхронизации:" in result.stdout:
        print("✅ Демон запущен")
        if "ожидание команды" in result.stdout:
            print("Статус: Ожидание команды (активен)")
        elif "синхронизация" in result.stdout:
            print("Статус: Синхронизация")
    else:
        print("❌ Демон не запущен")
    
    print("\n=== Информация о диске ===\n")
    for line in result.stdout.split('\n'):
        if 'Всего:' in line or 'Занято:' in line or 'Свободно:' in line:
            print(line.strip())

if __name__ == "__main__":
    test_status()