# -*- coding: utf-8 -*-

import sys
import os
import time
import subprocess
import threading
from pathlib import Path
from PyQt6.QtWidgets import QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon, QAction, QPixmap, QPainter, QColor
from PyQt6.QtCore import QTimer, Qt
from monitor import YandexDiskMonitor
from utils import is_autostart_enabled, set_autostart, open_folder, show_logs

class YandexDiskTray:
    def __init__(self, app):
        self.app = app
        
        # Создаём папку для конфигов
        self.config_dir = Path.home() / ".config" / "yandex-disk-tray"
        self.config_dir.mkdir(exist_ok=True)
        
        # Создаём иконки
        self.icons = self.create_icons()
        
        # Создаём иконку в трее
        self.tray = QSystemTrayIcon()
        self.tray.setIcon(self.icons["default"])
        self.tray.setVisible(True)
        
        # Создаём меню
        self.create_menu()
        
        self.tray.setContextMenu(self.menu)
        
        # Запускаем монитор
        self.monitor = YandexDiskMonitor()
        self.monitor.status_changed.connect(self.update_status)
        self.monitor.warning.connect(self.show_warning)
        self.monitor.sync_progress.connect(self.show_warning)
        
        self.monitor_thread = threading.Thread(target=self.monitor.run, daemon=True)
        self.monitor_thread.start()
        
        # Таймер для обновления подсказки
        self.tooltip_timer = QTimer()
        self.tooltip_timer.timeout.connect(self.update_tooltip)
        self.tooltip_timer.start(10000)
        
        self.tray.setToolTip("Яндекс.Диск\nСтатус: загрузка...")
        
        # Проверяем при запуске
        QTimer.singleShot(1000, self.check_initial_status)
    
    def create_icons(self):
        """Создаёт цветные иконки для трея"""
        icons = {}
        size = 64
        
        colors = {
            "running": QColor(76, 175, 80),    # зеленый
            "waiting": QColor(255, 193, 7),    # желтый
            "stopped": QColor(158, 158, 158),  # серый
            "error": QColor(244, 67, 54),      # красный
            "default": QColor(33, 150, 243)    # синий
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
            
            # Добавляем букву "Я"
            painter.setPen(QColor(255, 255, 255))
            font = painter.font()
            font.setPointSize(24)
            font.setBold(True)
            painter.setFont(font)
            painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "Я")
            
            painter.end()
            
            icons[name] = QIcon(pixmap)
        
        return icons
    
    def create_menu(self):
        """Создаёт меню трея"""
        self.menu = QMenu()
        
        # Статус (неактивный пункт)
        self.status_action = QAction("Статус: проверка...")
        self.status_action.setEnabled(False)
        self.menu.addAction(self.status_action)
        
        self.menu.addSeparator()
        
        # Кнопки управления
        self.pause_action = QAction("⏸️ Пауза")
        self.pause_action.triggered.connect(self.on_pause_sync)
        self.menu.addAction(self.pause_action)
        
        self.resume_action = QAction("▶️ Возобновить")
        self.resume_action.triggered.connect(self.on_resume_sync)
        self.menu.addAction(self.resume_action)
        
        self.sync_action = QAction("🔄 Принудительная синхронизация")
        self.sync_action.triggered.connect(self.on_force_sync)
        self.menu.addAction(self.sync_action)
        
        self.restart_action = QAction("🔁 Перезапустить")
        self.restart_action.triggered.connect(self.on_restart_disk)
        self.menu.addAction(self.restart_action)
        
        self.menu.addSeparator()
        
        # Навигация
        self.open_action = QAction("📂 Открыть папку")
        self.open_action.triggered.connect(self.on_open_folder)
        self.menu.addAction(self.open_action)
        
        self.logs_action = QAction("📋 Посмотреть логи")
        self.logs_action.triggered.connect(self.on_show_logs)
        self.menu.addAction(self.logs_action)
        
        self.menu.addSeparator()
        
        # Настройки автозапуска
        self.autostart_action = QAction("✅ Автозапуск")
        self.autostart_action.setCheckable(True)
        self.autostart_action.setChecked(is_autostart_enabled())
        self.autostart_action.triggered.connect(self.on_toggle_autostart)
        self.menu.addAction(self.autostart_action)
        
        self.menu.addSeparator()
        
        # Выход
        self.quit_action = QAction("🚪 Выход")
        self.quit_action.triggered.connect(self.on_quit)
        self.menu.addAction(self.quit_action)
    
    def check_initial_status(self):
        """Проверяет статус при запуске"""
        if not self.monitor.check_disk_running():
            self.show_warning("Yandex.Disk не запущен. Запускаю...")
            self.monitor.start_disk()
    
    def update_status(self, status_code, status_text):
        """Обновляет отображение статуса"""
        self.status_action.setText(f"Статус: {status_text}")
        
        # Меняем иконку в зависимости от статуса
        if status_code in self.icons:
            self.tray.setIcon(self.icons[status_code])
        else:
            self.tray.setIcon(self.icons["default"])
        
        self.update_tooltip()
        
        # Показываем уведомление об изменении статуса
        if status_code == "running":
            self.show_warning("🟢 Синхронизация активна")
        elif status_code == "waiting":
            self.show_warning("🟡 Ожидание команд")
        elif status_code == "stopped":
            self.show_warning("🔴 Синхронизация остановлена")
        elif status_code == "error":
            self.show_warning("⚠️ Ошибка синхронизации")
    
    def update_tooltip(self):
        """Обновляет подсказку при наведении"""
        try:
            # Получаем информацию о диске
            usage = self.monitor.get_disk_usage()
            
            # Получаем статус
            status_text = self.status_action.text().replace("Статус: ", "")
            
            # Формируем подсказку
            tooltip = f"Яндекс.Диск\n{status_text}"
            if usage:
                tooltip += f"\n\n{usage}"
            
            self.tray.setToolTip(tooltip)
        except Exception as e:
            print(f"Ошибка обновления подсказки: {e}")
    
    def show_warning(self, message):
        """Показывает всплывающее уведомление"""
        try:
            self.tray.showMessage(
                "Яндекс.Диск",
                message,
                self.icons["default"],
                5000  # 5 секунд
            )
        except Exception as e:
            print(f"Ошибка показа уведомления: {e}")
    
    def on_pause_sync(self):
        """Останавливает синхронизацию (ручная остановка)"""
        try:
            # Устанавливаем флаг ручной остановки, чтобы монитор не перезапускал диск
            self.monitor.set_manual_stop(True)
            subprocess.run(["yandex-disk", "stop"], 
                         stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL)
            self.show_warning("⏸️ Синхронизация приостановлена")
        except Exception as e:
            self.show_warning(f"Ошибка: {e}")
    
    def on_resume_sync(self):
        """Возобновляет синхронизацию"""
        try:
            # Снимаем флаг ручной остановки
            self.monitor.set_manual_stop(False)
            subprocess.run(["yandex-disk", "start"], 
                         stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL)
            self.show_warning("▶️ Синхронизация возобновлена")
        except Exception as e:
            self.show_warning(f"Ошибка: {e}")
    
    def on_force_sync(self):
        """Принудительная синхронизация"""
        try:
            self.monitor.force_sync_now()
        except Exception as e:
            self.show_warning(f"Ошибка: {e}")
    
    def on_restart_disk(self):
        """Перезапускает Yandex.Disk"""
        try:
            self.show_warning("🔄 Перезапуск Yandex.Disk...")
            # Снимаем флаг ручной остановки при перезапуске
            self.monitor.set_manual_stop(False)
            subprocess.run(["yandex-disk", "stop"], 
                         stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL)
            time.sleep(2)
            subprocess.run(["yandex-disk", "start"], 
                         stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL)
            self.show_warning("✅ Перезапуск выполнен")
        except Exception as e:
            self.show_warning(f"Ошибка: {e}")
    
    def on_open_folder(self):
        """Открывает папку Яндекс.Диска в файловом менеджере"""
        open_folder()
    
    def on_show_logs(self):
        """Показывает логи и информацию о статусе"""
        show_logs(self.config_dir)
    
    def on_toggle_autostart(self, checked):
        """Включает/выключает автозапуск программы"""
        set_autostart(checked, sys.argv[0])
        
        if checked:
            self.show_warning("✅ Автозапуск включен\nПрограмма будет запускаться при входе в систему")
        else:
            self.show_warning("❌ Автозапуск выключен")
    
    def on_quit(self):
        """Выход из приложения"""
        self.monitor.stop()
        self.app.quit()