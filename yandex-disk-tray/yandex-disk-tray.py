#!/usr/bin/env python3
# yandex-disk-tray.py

import sys
import subprocess
import os
import time
import threading
from pathlib import Path
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QMessageBox
from PyQt6.QtGui import QIcon, QAction, QPixmap, QPainter, QColor
from PyQt6.QtCore import QTimer, pyqtSignal, QObject, Qt

class YandexDiskMonitor(QObject):
    """Класс для мониторинга Yandex.Disk в отдельном потоке"""
    status_changed = pyqtSignal(str, str)  # status_code, status_text
    warning = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.running = True
        self.last_status = None
        self.start_attempts = 0
        self.max_start_attempts = 3
        
    def stop(self):
        self.running = False
        
    def check_disk_running(self):
        """Проверяет, запущен ли процесс yandex-disk"""
        try:
            result = subprocess.run(
                "pgrep -f 'yandex-disk' | grep -v 'pgrep' | grep -v 'python'",
                shell=True,
                capture_output=True,
                text=True
            )
            return result.stdout.strip() != ""
        except:
            return False
    
    def start_disk(self):
        """Запускает yandex-disk"""
        try:
            subprocess.run("yandex-disk start", shell=True, timeout=5)
            return True
        except:
            return False
    
    def get_status(self):
        """Получает статус yandex-disk"""
        try:
            result = subprocess.run(
                "yandex-disk status",
                shell=True,
                capture_output=True,
                text=True,
                timeout=5
            )
            status = result.stdout.strip()
            
            if "synchronization process is running" in status:
                return "running", "🟢 Синхронизация"
            elif "synchronization process is stopped" in status:
                return "stopped", "🔴 Остановлен"
            elif "error" in status.lower() or "not" in status.lower():
                return "error", "⚠️ Ошибка"
            else:
                return "unknown", "⚪ Неизвестно"
        except subprocess.TimeoutExpired:
            return "timeout", "⏰ Таймаут"
        except:
            return "error", "⚠️ Ошибка"
    
    def run(self):
        """Основной цикл мониторинга"""
        start_time = None
        warning_shown = False
        
        while self.running:
            try:
                # Проверяем запущен ли процесс
                if not self.check_disk_running():
                    self.warning.emit("❌ Yandex.Disk не запущен! Запускаю...")
                    self.start_disk()
                    start_time = time.time()
                    warning_shown = False
                    time.sleep(2)
                    continue
                
                # Получаем статус
                status_code, status_text = self.get_status()
                
                # Проверяем таймаут запуска
                if status_code != "running" and start_time is not None:
                    elapsed = time.time() - start_time
                    if elapsed > 5 and not warning_shown:
                        self.warning.emit(
                            f"⚠️ Yandex.Disk не запускается более 5 секунд!\n"
                            f"Текущий статус: {status_text}\n"
                            f"Попробуйте проверить логи: yandex-disk log"
                        )
                        warning_shown = True
                        self.start_attempts += 1
                        
                        # Если много попыток - пробуем перезапустить
                        if self.start_attempts >= self.max_start_attempts:
                            self.warning.emit("🔄 Перезапускаю Yandex.Disk...")
                            subprocess.run("yandex-disk stop", shell=True)
                            time.sleep(2)
                            self.start_disk()
                            self.start_attempts = 0
                            start_time = time.time()
                
                # Если статус изменился - сообщаем
                if status_code != self.last_status:
                    self.status_changed.emit(status_code, status_text)
                    self.last_status = status_code
                
                time.sleep(2)
            except Exception as e:
                print(f"Ошибка в мониторе: {e}")
                time.sleep(5)

class YandexDiskTray:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)
        
        # Создаём папку для конфигов если нет
        self.config_dir = Path.home() / ".config" / "yandex-disk-tray"
        self.config_dir.mkdir(exist_ok=True)
        
        # Создаём иконки
        self.icons = self.create_icons()
        
        # Создаём иконку в трее
        self.tray = QSystemTrayIcon()
        self.tray.setIcon(self.icons["default"])
        self.tray.setVisible(True)
        
        # Создаём меню
        self.menu = QMenu()
        
        # Статус
        self.status_action = QAction("Статус: проверка...")
        self.status_action.setEnabled(False)
        self.menu.addAction(self.status_action)
        
        self.menu.addSeparator()
        
        # Кнопки управления
        self.pause_action = QAction("⏸️ Пауза")
        self.pause_action.triggered.connect(self.pause_sync)
        self.menu.addAction(self.pause_action)
        
        self.resume_action = QAction("▶️ Возобновить")
        self.resume_action.triggered.connect(self.resume_sync)
        self.menu.addAction(self.resume_action)
        
        self.restart_action = QAction("🔄 Перезапустить")
        self.restart_action.triggered.connect(self.restart_disk)
        self.menu.addAction(self.restart_action)
        
        self.menu.addSeparator()
        
        self.open_action = QAction("📂 Открыть папку")
        self.open_action.triggered.connect(self.open_folder)
        self.menu.addAction(self.open_action)
        
        self.logs_action = QAction("📋 Посмотреть логи")
        self.logs_action.triggered.connect(self.show_logs)
        self.menu.addAction(self.logs_action)
        
        self.menu.addSeparator()
        
        # Настройки автозапуска
        self.autostart_action = QAction("✅ Автозапуск")
        self.autostart_action.setCheckable(True)
        self.autostart_action.setChecked(self.is_autostart_enabled())
        self.autostart_action.triggered.connect(self.toggle_autostart)
        self.menu.addAction(self.autostart_action)
        
        self.menu.addSeparator()
        
        self.quit_action = QAction("🚪 Выход")
        self.quit_action.triggered.connect(self.quit)
        self.menu.addAction(self.quit_action)
        
        self.tray.setContextMenu(self.menu)
        
        # Запускаем монитор в отдельном потоке
        self.monitor = YandexDiskMonitor()
        self.monitor.status_changed.connect(self.update_status)
        self.monitor.warning.connect(self.show_warning)
        
        self.monitor_thread = threading.Thread(target=self.monitor.run, daemon=True)
        self.monitor_thread.start()
        
        # Таймер для обновления подсказки
        self.tooltip_timer = QTimer()
        self.tooltip_timer.timeout.connect(self.update_tooltip)
        self.tooltip_timer.start(10000)  # каждые 10 секунд
        
        # Показываем подсказку
        self.tray.setToolTip("Яндекс.Диск\nСтатус: загрузка...")
        
        # Проверяем при запуске
        QTimer.singleShot(1000, self.check_initial_status)
    
    def create_icons(self):
        """Создаёт цветные иконки для трея"""
        icons = {}
        size = 64  # размер иконки
        
        colors = {
            "running": QColor(76, 175, 80),    # зеленый
            "stopped": QColor(158, 158, 158),  # серый
            "error": QColor(244, 67, 54),       # красный
            "default": QColor(33, 150, 243)     # синий
        }
        
        for name, color in colors.items():
            pixmap = QPixmap(size, size)
            pixmap.fill(Qt.GlobalColor.transparent)
            
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            # Рисуем круг
            painter.setBrush(color)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(4, 4, size-8, size-8)
            
            # Добавляем букву "Я" для узнаваемости
            painter.setPen(QColor(255, 255, 255))
            font = painter.font()
            font.setPointSize(24)
            font.setBold(True)
            painter.setFont(font)
            painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "Я")
            
            painter.end()
            
            icons[name] = QIcon(pixmap)
        
        return icons
    
    def check_initial_status(self):
        """Проверяет статус при запуске"""
        if not self.monitor.check_disk_running():
            self.show_warning("Yandex.Disk не запущен. Запускаю...")
            self.monitor.start_disk()
    
    def update_status(self, status_code, status_text):
        """Обновляет отображение статуса"""
        self.status_action.setText(f"Статус: {status_text}")
        
        # Устанавливаем иконку
        if status_code in self.icons:
            self.tray.setIcon(self.icons[status_code])
        else:
            self.tray.setIcon(self.icons["default"])
        
        self.update_tooltip()
    
    def update_tooltip(self):
        """Обновляет подсказку"""
        try:
            # Получаем дополнительную информацию
            usage = subprocess.run(
                "yandex-disk usage",
                shell=True,
                capture_output=True,
                text=True,
                timeout=2
            ).stdout.strip()
            
            # Получаем статус для подсказки
            status_text = self.status_action.text().replace("Статус: ", "")
            
            tooltip = f"Яндекс.Диск\n{status_text}"
            if usage:
                # Форматируем usage для читаемости
                lines = usage.split('\n')
                for line in lines:
                    if 'total' in line or 'free' in line or 'used' in line:
                        tooltip += f"\n{line.strip()}"
            
            self.tray.setToolTip(tooltip)
        except Exception as e:
            print(f"Ошибка обновления подсказки: {e}")
    
    def show_warning(self, message):
        """Показывает предупреждение"""
        try:
            self.tray.showMessage(
                "Яндекс.Диск",
                message,
                self.icons["default"],
                5000  # 5 секунд
            )
        except Exception as e:
            print(f"Ошибка показа уведомления: {e}")
    
    def pause_sync(self):
        """Останавливает синхронизацию"""
        try:
            subprocess.run("yandex-disk stop", shell=True)
            self.show_warning("Синхронизация приостановлена")
        except Exception as e:
            self.show_warning(f"Ошибка: {e}")
    
    def resume_sync(self):
        """Возобновляет синхронизацию"""
        try:
            subprocess.run("yandex-disk start", shell=True)
            self.show_warning("Синхронизация возобновлена")
        except Exception as e:
            self.show_warning(f"Ошибка: {e}")
    
    def restart_disk(self):
        """Перезапускает Yandex.Disk"""
        try:
            self.show_warning("Перезапуск Yandex.Disk...")
            subprocess.run("yandex-disk stop", shell=True)
            time.sleep(2)
            subprocess.run("yandex-disk start", shell=True)
        except Exception as e:
            self.show_warning(f"Ошибка: {e}")
    
    def open_folder(self):
        """Открывает папку Яндекс.Диска"""
        # Пробуем найти папку
        possible_paths = [
            os.path.expanduser("~/Yandex.Disk"),
            os.path.expanduser("~/yandex.disk"),
            os.path.expanduser("~/Яндекс.Диск")
        ]
        
        for folder in possible_paths:
            if os.path.exists(folder):
                try:
                    subprocess.run(f'xdg-open "{folder}"', shell=True)
                    return
                except:
                    pass
        
        # Если не нашли, показываем предупреждение
        self.show_warning("Папка Яндекс.Диска не найдена")
    
    def show_logs(self):
        """Показывает логи в терминале"""
        try:
            # Пробуем разные терминалы
            terminals = [
                "gnome-terminal --",
                "xterm -e",
                "konsole -e",
                "xfce4-terminal -e"
            ]
            
            log_script = self.config_dir / "show_logs.sh"
            with open(log_script, "w") as f:
                f.write("""#!/bin/bash
echo "=== Логи Yandex.Disk ==="
echo
yandex-disk log 2>&1
echo
echo "Нажмите Enter для закрытия..."
read
""")
            os.chmod(log_script, 0o755)
            
            for term in terminals:
                try:
                    subprocess.Popen(f'{term} "{log_script}"', shell=True)
                    return
                except:
                    continue
            
            self.show_warning("Не удалось открыть терминал")
        except Exception as e:
            self.show_warning(f"Ошибка: {e}")
    
    def is_autostart_enabled(self):
        """Проверяет, включен ли автозапуск"""
        autostart_file = Path.home() / ".config" / "autostart" / "yandex-disk-tray.desktop"
        return autostart_file.exists()
    
    def toggle_autostart(self, checked):
        """Включает/выключает автозапуск"""
        autostart_dir = Path.home() / ".config" / "autostart"
        autostart_dir.mkdir(exist_ok=True)
        
        autostart_file = autostart_dir / "yandex-disk-tray.desktop"
        
        if checked:
            # Создаём .desktop файл для автозапуска
            desktop_content = f"""[Desktop Entry]
Type=Application
Name=Yandex.Disk Tray
Comment=GUI для Яндекс.Диска
Exec={sys.argv[0]}
Icon=yandex-disk
Terminal=false
Categories=Network;FileTransfer;
X-GNOME-Autostart-enabled=true
"""
            with open(autostart_file, "w") as f:
                f.write(desktop_content)
            self.show_warning("Автозапуск включен")
        else:
            # Удаляем файл автозапуска
            if autostart_file.exists():
                autostart_file.unlink()
            self.show_warning("Автозапуск выключен")
    
    def quit(self):
        """Выход из приложения"""
        self.monitor.stop()
        self.app.quit()

if __name__ == "__main__":
    # Проверяем наличие yandex-disk
    try:
        result = subprocess.run("which yandex-disk", shell=True, capture_output=True, text=True)
        if not result.stdout:
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Icon.Critical)
            msg_box.setWindowTitle("Ошибка")
            msg_box.setText("yandex-disk не установлен!")
            msg_box.setInformativeText(
                "Установите его:\n"
                "sudo apt install yandex-disk  # для Ubuntu/Debian\n"
                "или скачайте с https://disk.yandex.ru/download"
            )
            msg_box.exec()
            sys.exit(1)
    except:
        pass
    
    app = YandexDiskTray()
    sys.exit(app.app.exec())