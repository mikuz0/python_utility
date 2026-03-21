# -*- coding: utf-8 -*-

import os
from pathlib import Path

# Версия приложения
VERSION = "1.0.0"

# Пути
HOME = Path.home()
CONFIG_DIR = HOME / ".config" / "yandex-disk-tray"
AUTOSTART_DIR = HOME / ".config" / "autostart"
AUTOSTART_FILE = AUTOSTART_DIR / "yandex-disk-tray.desktop"

# Настройки по умолчанию
CHECK_INTERVAL = 2  # секунды
WARNING_TIMEOUT = 5  # секунды
MAX_RESTART_ATTEMPTS = 3

# Возможные пути к папке Яндекс.Диска
YANDEX_DISK_PATHS = [
    HOME / "Yandex.Disk",
    HOME / "yandex.disk",
    HOME / "Яндекс.Диск"
]

# Терминалы для показа логов
TERMINALS = [
    "gnome-terminal --",
    "xterm -e",
    "konsole -e",
    "xfce4-terminal -e"
]