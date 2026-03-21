# -*- coding: utf-8 -*-

import os
import subprocess
from pathlib import Path

def is_autostart_enabled():
    """
    Проверяет, включен ли автозапуск программы
    
    Returns:
        bool: True если автозапуск включен, False если выключен
    """
    autostart_file = Path.home() / ".config" / "autostart" / "yandex-disk-tray.desktop"
    return autostart_file.exists()

def set_autostart(enabled, script_path):
    """
    Включает или выключает автозапуск программы
    
    Args:
        enabled (bool): True - включить автозапуск, False - выключить
        script_path (str): путь к скрипту программы
    """
    autostart_dir = Path.home() / ".config" / "autostart"
    autostart_dir.mkdir(exist_ok=True)
    
    autostart_file = autostart_dir / "yandex-disk-tray.desktop"
    
    if enabled:
        # Создаём .desktop файл для автозапуска
        desktop_content = f"""[Desktop Entry]
Type=Application
Name=Yandex.Disk Tray
Comment=GUI для Яндекс.Диска
Exec={script_path}
Icon=yandex-disk
Terminal=false
Categories=Network;FileTransfer;
X-GNOME-Autostart-enabled=true
"""
        with open(autostart_file, "w", encoding='utf-8') as f:
            f.write(desktop_content)
        print(f"✅ Автозапуск включен: {autostart_file}")
    else:
        # Удаляем файл автозапуска
        if autostart_file.exists():
            autostart_file.unlink()
            print(f"❌ Автозапуск выключен: {autostart_file}")

def open_folder():
    """
    Открывает папку Яндекс.Диска в стандартном файловом менеджере
    
    Returns:
        bool: True если папка найдена и открыта, False если не найдена
    """
    possible_paths = [
        os.path.expanduser("~/Yandex.Disk"),
        os.path.expanduser("~/yandex.disk"),
        os.path.expanduser("~/Яндекс.Диск")
    ]
    
    for folder in possible_paths:
        if os.path.exists(folder):
            try:
                subprocess.run(['xdg-open', folder], 
                             stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL)
                return True
            except Exception as e:
                print(f"Ошибка открытия папки {folder}: {e}")
                continue
    
    print("Папка Яндекс.Диска не найдена")
    return False

def show_logs(config_dir):
    """
    Показывает информацию о статусе Yandex.Disk в терминале
    
    Args:
        config_dir (Path): директория для временных файлов
    """
    try:
        # Создаём временный скрипт для показа информации
        log_script = config_dir / "show_logs.sh"
        with open(log_script, "w", encoding='utf-8') as f:
            f.write("""#!/bin/bash
echo "=========================================="
echo "        Информация о Yandex.Disk          "
echo "=========================================="
echo
echo "1. Статус синхронизации:"
echo "------------------------------------------"
yandex-disk status
echo
echo "2. Процессы Yandex.Disk:"
echo "------------------------------------------"
ps aux | grep yandex-disk | grep -v grep
echo
echo "3. Версия Yandex.Disk:"
echo "------------------------------------------"
yandex-disk --version
echo
echo "=========================================="
echo "Нажмите Enter для закрытия..."
read
""")
        os.chmod(log_script, 0o755)
        
        # Пробуем открыть в разных терминалах
        terminals = [
            ("gnome-terminal", "gnome-terminal --"),
            ("konsole", "konsole -e"),
            ("xfce4-terminal", "xfce4-terminal -e"),
            ("xterm", "xterm -e")
        ]
        
        opened = False
        for term_name, term_cmd in terminals:
            try:
                # Проверяем, установлен ли терминал
                subprocess.run(["which", term_name], 
                             capture_output=True, 
                             check=True)
                # Запускаем скрипт в терминале
                subprocess.Popen(f'{term_cmd} "{log_script}"', shell=True)
                opened = True
                break
            except (subprocess.CalledProcessError, FileNotFoundError):
                continue
        
        # Если ни один терминал не открылся, показываем в текущем
        if not opened:
            print("Не удалось открыть терминал. Показываю в текущем окне:")
            subprocess.run(['bash', str(log_script)])
            
    except Exception as e:
        print(f"Ошибка при показе логов: {e}")

def get_disk_usage():
    """
    Получает информацию об использовании диска из yandex-disk status
    
    Returns:
        str: строка с информацией о диске (Всего, Занято, Свободно)
    """
    try:
        result = subprocess.run(
            ["yandex-disk", "status"],
            capture_output=True,
            text=True,
            timeout=2
        )
        output = result.stdout
        
        # Парсим русские строки с информацией о диске
        usage_lines = []
        for line in output.split('\n'):
            line = line.strip()
            if 'Всего:' in line or 'Занято:' in line or 'Свободно:' in line:
                usage_lines.append(line)
            elif 'Total:' in line or 'Used:' in line or 'Free:' in line:
                usage_lines.append(line)
        
        if usage_lines:
            return '\n'.join(usage_lines)
        return ""
    except Exception as e:
        print(f"Ошибка получения информации о диске: {e}")
        return ""