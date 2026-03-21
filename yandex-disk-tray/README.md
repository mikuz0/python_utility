README.md (полное описание проекта)
markdown

# Yandex.Disk Tray

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![PyQt6](https://img.shields.io/badge/PyQt6-6.4.0-green.svg)](https://pypi.org/project/PyQt6/)
[![License](https://img.shields.io/badge/license-GPLv3-red.svg)](LICENSE)
[![Linux](https://img.shields.io/badge/platform-Linux-yellow.svg)](https://www.linux.org/)

**Графический индикатор для Яндекс.Диска в системном трее Linux**

## 📋 Оглавление

- [Описание](#-описание)
- [Возможности](#-возможности)
- [Скриншоты](#-скриншоты)
- [Требования](#-требования)
- [Установка](#-установка)
- [Настройка](#-настройка)
- [Использование](#-использование)
- [Архитектура](#-архитектура)
- [Управление](#-управление)
- [Устранение неполадок](#-устранение-неполадок)
- [Разработка](#-разработка)
- [Лицензия](#-лицензия)

---

## 📝 Описание

**Yandex.Disk Tray** — это легковесный графический индикатор для официального консольного клиента Яндекс.Диска (`yandex-disk`). Программа добавляет иконку в системный трей, отображает статус синхронизации и позволяет управлять работой Яндекс.Диска без использования терминала.

Программа написана на Python с использованием PyQt6 и предназначена для работы в любом Linux окружении (GNOME, KDE, XFCE, и др.).

---

## ✨ Возможности

### Основные функции
- 🟢 **Визуальный индикатор** — цветная иконка в трее показывает статус синхронизации
- 🔄 **Автоматический запуск** — программа запускает `yandex-disk` если он не активен
- ⏱️ **Мониторинг таймаутов** — предупреждение если диск не запускается более 5 секунд
- 🚀 **Автозагрузка** — возможность запуска программы при входе в систему
- 📋 **Просмотр логов** — быстрый доступ к статусу и логам Яндекс.Диска
- 📂 **Быстрое открытие папки** — открытие папки Яндекс.Диска в файловом менеджере

### Цветовая индикация
| Цвет | Статус | Описание |
|------|--------|----------|
| 🟢 Зелёный | Синхронизация | Активная синхронизация файлов |
| 🟡 Жёлтый | Ожидание | Демон работает, ожидает команды |
| 🔴 Серый | Остановлен | Синхронизация остановлена |
| 🔴 Красный | Ошибка | Ошибка синхронизации или процесс не отвечает |
| 🔵 Синий | Загрузка | Начальная загрузка или неопределённый статус |

### Меню программы

┌─────────────────────────────────────┐
│ Статус: 🟢 Синхронизация │
├─────────────────────────────────────┤
│ ⏸️ Пауза │
│ ▶️ Возобновить │
│ 🔄 Принудительная синхронизация │
│ 🔁 Перезапустить │
├─────────────────────────────────────┤
│ 📂 Открыть папку │
│ 📋 Посмотреть логи │
├─────────────────────────────────────┤
│ ✅ Автозапуск (галочка) │
├─────────────────────────────────────┤
│ 🚪 Выход │
└─────────────────────────────────────┘
text


---

## 📸 Скриншоты

### Иконка в трее

🔵 - синяя иконка при запуске
🟢 - зелёная иконка при активной синхронизации
🟡 - жёлтая иконка при ожидании
text


### Всплывающее меню

[Иконка] Яндекс.Диск
🟢 Синхронизация активна
Всего: 31.12 GB
Занято: 13.59 GB
Свободно: 17.53 GB
text


### Уведомления

┌─────────────────────────────────────┐
│ 🤖 Яндекс.Диск │
│ │
│ ✅ Синхронизация возобновлена │
└─────────────────────────────────────┘
text


---

## 📦 Требования

### Системные требования
- **Операционная система:** Linux (Ubuntu, Debian, Fedora, Arch, и др.)
- **Python:** версия 3.8 или выше
- **Дисплейный менеджер:** поддержка системного трея (GNOME, KDE, XFCE)

### Зависимости
| Пакет | Назначение |
|-------|------------|
| `yandex-disk` | Официальный консольный клиент |
| `PyQt6` | Графический фреймворк |
| `python3-pyqt6` | Python биндинги для PyQt6 |
| `xdg-utils` | Открытие папок и файлов |
| `libnotify-bin` | Системные уведомления |
| `zenity` (опционально) | Диалоговые окна |

---

## 🔧 Установка

### 1. Установка зависимостей

#### Ubuntu/Debian
```bash
# Обновление пакетов
sudo apt update

# Установка yandex-disk (официальный репозиторий)
echo "deb http://repo.yandex.ru/yandex-disk/deb/ stable main" | sudo tee /etc/apt/sources.list.d/yandex-disk.list
wget http://repo.yandex.ru/yandex-disk/YANDEX-DISCH-KEY.GPG -O- | sudo apt-key add -
sudo apt update
sudo apt install yandex-disk

# Установка Python и PyQt6
sudo apt install python3 python3-pip python3-pyqt6

# Установка дополнительных утилит
sudo apt install xdg-utils libnotify-bin zenity

Fedora/RHEL
bash

# Установка yandex-disk
sudo dnf install https://repo.yandex.ru/yandex-disk/rpm/stable/x86_64/yandex-disk-1.0.2-1.x86_64.rpm

# Установка Python и PyQt6
sudo dnf install python3 python3-pip python3-qt6

# Установка дополнительных утилит
sudo dnf install xdg-utils libnotify zenity

Arch Linux
bash

# Установка yandex-disk
yay -S yandex-disk

# Установка Python и PyQt6
sudo pacman -S python python-pip python-pyqt6

# Установка дополнительных утилит
sudo pacman -S xdg-utils libnotify zenity

2. Установка программы
bash

# Клонирование репозитория
git clone https://github.com/yourusername/yandex-disk-tray.git
cd yandex-disk-tray

# Установка через pip (рекомендуется)
pip install --user .

# Или запуск напрямую
python3 main.py

3. Настройка yandex-disk (первый запуск)
bash

# Запуск мастера настройки
yandex-disk setup

# Следуйте инструкциям:
# - Войдите в свой аккаунт Яндекс
# - Разрешите доступ
# - Укажите путь к папке (по умолчанию ~/Yandex.Disk)

⚙️ Настройка
Автозапуск программы

Программа автоматически добавляет себя в автозагрузку при установке галочки в меню. Файл автозапуска сохраняется в:
text

~/.config/autostart/yandex-disk-tray.desktop

Ручная настройка автозапуска
bash

# Создание файла автозапуска вручную
mkdir -p ~/.config/autostart
cat > ~/.config/autostart/yandex-disk-tray.desktop << EOF
[Desktop Entry]
Type=Application
Name=Yandex.Disk Tray
Comment=GUI для Яндекс.Диска
Exec=$HOME/.local/bin/yandex-disk-tray
Icon=yandex-disk
Terminal=false
Categories=Network;FileTransfer;
X-GNOME-Autostart-enabled=true
EOF

Настройка иконок

Если иконки не отображаются, создайте их вручную:
bash

# Создание иконок
mkdir -p ~/.local/share/icons/hicolor/scalable/apps

# Зелёная иконка (синхронизация)
cat > ~/.local/share/icons/hicolor/scalable/apps/yandex-disk-running.svg << 'EOF'
<svg width="128" height="128" xmlns="http://www.w3.org/2000/svg">
 <circle cx="64" cy="64" r="56" fill="#4caf50"/>
 <text x="64" y="86" font-size="48" text-anchor="middle" fill="white">Я</text>
</svg>
EOF

# Жёлтая иконка (ожидание)
cat > ~/.local/share/icons/hicolor/scalable/apps/yandex-disk-waiting.svg << 'EOF'
<svg width="128" height="128" xmlns="http://www.w3.org/2000/svg">
 <circle cx="64" cy="64" r="56" fill="#ffc107"/>
 <text x="64" y="86" font-size="48" text-anchor="middle" fill="white">Я</text>
</svg>
EOF

# Серая иконка (остановлен)
cat > ~/.local/share/icons/hicolor/scalable/apps/yandex-disk-paused.svg << 'EOF'
<svg width="128" height="128" xmlns="http://www.w3.org/2000/svg">
 <circle cx="64" cy="64" r="56" fill="#9e9e9e"/>
 <text x="64" y="86" font-size="48" text-anchor="middle" fill="white">Я</text>
</svg>
EOF

# Обновление кэша иконок
gtk-update-icon-cache -f ~/.local/share/icons/hicolor

🖱️ Использование
Запуск программы
bash

# Запуск из терминала (для отладки)
python3 main.py

# Запуск в фоне
python3 main.py &

# Запуск через установленную команду
yandex-disk-tray

Управление через меню

    Клик правой кнопкой по иконке в трее

    Выберите нужное действие:

        Пауза — остановка синхронизации (диск не перезапускается автоматически)

        Возобновить — запуск синхронизации

        Принудительная синхронизация — немедленная синхронизация всех файлов

        Перезапустить — остановка и запуск Яндекс.Диска

        Открыть папку — открытие папки Яндекс.Диска в файловом менеджере

        Посмотреть логи — отображение статуса и процессов в терминале

        Автозапуск — добавление/удаление программы из автозагрузки

        Выход — закрытие программы

Горячие клавиши

Программа не имеет горячих клавиш, но вы можете назначить их в настройках вашего окружения рабочего стола.
🏗️ Архитектура
Структура проекта
text

yandex-disk-tray/
├── main.py                 # Точка входа
├── tray_icon.py           # Класс иконки в трее
├── monitor.py             # Мониторинг Яндекс.Диска
├── utils.py               # Вспомогательные функции
├── requirements.txt       # Зависимости
├── setup.py               # Установка
├── yandex-disk-tray.desktop # Файл автозапуска
└── README.md              # Документация

Компоненты
Компонент	Назначение
main.py	Инициализация приложения, проверка зависимостей
tray_icon.py	Создание и управление иконкой в трее, меню, обработка действий пользователя
monitor.py	Фоновый мониторинг процесса yandex-disk, проверка статуса, автоматический запуск
utils.py	Вспомогательные функции: автозапуск, открытие папки, логи
Диаграмма архитектуры
text

┌─────────────────────────────────────────────────────────────┐
│                       Yandex.Disk Tray                      │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│  │  main.py    │───▶│ tray_icon.py│───▶│  monitor.py │     │
│  └─────────────┘    └─────────────┘    └─────────────┘     │
│         │                 │                   │             │
│         ▼                 ▼                   ▼             │
│  ┌─────────────────────────────────────────────────┐       │
│  │                  utils.py                       │       │
│  └─────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │  yandex-disk    │
                    │  (CLI client)   │
                    └─────────────────┘

🎮 Управление
Команды для управления Яндекс.Диском
Команда	Описание
yandex-disk start	Запуск демона синхронизации
yandex-disk stop	Остановка демона
yandex-disk status	Просмотр статуса и информации
yandex-disk sync	Принудительная синхронизация
yandex-disk setup	Первоначальная настройка
Проверка статуса в терминале
bash

# Просмотр статуса
yandex-disk status

# Просмотр процессов
ps aux | grep yandex-disk

# Просмотр логов (через journalctl)
journalctl -u yandex-disk --no-pager -n 50

🐛 Устранение неполадок
Иконка не появляется в трее

Проблема: Иконка программы не отображается в системном трее.

Решение:
bash

# Проверка окружения
echo $XDG_CURRENT_DESKTOP

# Для GNOME: установите расширение AppIndicator
sudo apt install gnome-shell-extension-appindicator
gnome-extensions enable appindicatorsupport@rgcjonas.gmail.com

# Для KDE: добавьте виджет System Tray
# Правой кнопкой на панель -> Добавить виджеты -> System Tray

Статус не обновляется

Проблема: Иконка показывает неправильный статус.

Решение:
bash

# Проверка работы yandex-disk
yandex-disk status

# Перезапуск монитора
pkill -f yandex-disk-tray
python3 main.py

# Проверка прав доступа
ls -la ~/.config/yandex-disk/

Автозапуск не работает

Проблема: Программа не запускается при входе в систему.

Решение:
bash

# Проверка существования файла
ls -la ~/.config/autostart/yandex-disk-tray.desktop

# Проверка прав доступа
chmod +x ~/.config/autostart/yandex-disk-tray.desktop

# Проверка содержимого
cat ~/.config/autostart/yandex-disk-tray.desktop

# Ручное добавление (см. раздел "Настройка")

Ошибка "yandex-disk not found"

Проблема: Программа не находит установленный yandex-disk.

Решение:
bash

# Проверка установки
which yandex-disk

# Установка yandex-disk
sudo apt install yandex-disk

# Перенастройка
yandex-disk setup

Пауза не работает (диск перезапускается)

Проблема: При нажатии "Пауза" диск останавливается, но сразу перезапускается.

Решение: Это исправлено в последней версии. Обновите программу:
bash

git pull
pip install --user --upgrade .

🛠️ Разработка
Установка для разработки
bash

# Клонирование репозитория
git clone https://github.com/yourusername/yandex-disk-tray.git
cd yandex-disk-tray

# Создание виртуального окружения
python3 -m venv venv
source venv/bin/activate

# Установка зависимостей
pip install -r requirements.txt

# Запуск в режиме отладки
python3 main.py

Структура кода
python

# main.py - точка входа
def main():
    # Проверка зависимостей
    # Создание QApplication
    # Запуск YandexDiskTray

# tray_icon.py - GUI
class YandexDiskTray:
    def __init__(self):
        # Создание иконок
        # Создание меню
        # Запуск монитора

# monitor.py - бизнес-логика
class YandexDiskMonitor:
    def run(self):
        # Основной цикл мониторинга
        while self.running:
            # Проверка процесса
            # Получение статуса
            # Эмит сигналов

# utils.py - утилиты
def is_autostart_enabled(): ...
def set_autostart(): ...
def open_folder(): ...
def show_logs(): ...

Добавление новых функций

    Новая кнопка в меню:
    python

    # в tray_icon.py -> create_menu()
    new_action = QAction("✨ Новая функция")
    new_action.triggered.connect(self.on_new_function)
    self.menu.addAction(new_action)

    def on_new_function(self):
        # Реализация
        pass

    Новая команда в монитор:
    python

    # в monitor.py
    def new_command(self):
        try:
            subprocess.run(["yandex-disk", "new-command"])
        except Exception as e:
            print(f"Ошибка: {e}")

Тестирование
bash

# Ручное тестирование
python3 main.py

# Проверка статуса
yandex-disk status

# Проверка процессов
ps aux | grep yandex-disk

# Проверка автозапуска
ls -la ~/.config/autostart/

📄 Лицензия

Этот проект распространяется под лицензией GNU General Public License v3.0.
text

Yandex.Disk Tray - графический индикатор для Яндекс.Диска
Copyright (C) 2024

Это свободная программа: вы можете распространять и/или изменять её
на условиях Стандартной общественной лицензии GNU в том виде,
в каком она опубликована Фондом свободного программного обеспечения;
либо версии 3 лицензии, либо (по вашему выбору) любой более поздней версии.

Эта программа распространяется в надежде, что она будет полезной,
но БЕЗ ВСЯКИХ ГАРАНТИЙ; даже без подразумеваемой гарантии ТОВАРНОГО СОСТОЯНИЯ
или ПРИГОДНОСТИ ДЛЯ ОПРЕДЕЛЁННЫХ ЦЕЛЕЙ. См. Стандартную общественную лицензию GNU.

Полный текст лицензии: https://www.gnu.org/licenses/gpl-3.0.html
🤝 Вклад в проект

Приветствуются любые вклады в развитие проекта:

    🐛 Сообщения об ошибках — через Issues

    💡 Предложения по улучшению — через Discussions

    🔧 Pull requests — с новыми функциями или исправлениями

Планы на будущее

    Поддержка нескольких аккаунтов

    График синхронизации (пропуск определённых часов)

    Фильтрация файлов и папок

    Интеграция с файловыми менеджерами

    Настройка через графический интерфейс

    Поддержка Windows и macOS

📞 Контакты

    Автор: [Ваше имя]

    Email: [ваш email]

    GitHub: https://github.com/yourusername

🙏 Благодарности

    Яндекс — за официальный клиент yandex-disk

    Qt Project — за отличный фреймворк PyQt6

    Сообщество Linux — за поддержку и тестирование

Сделано с ❤️ для пользователей Linux
