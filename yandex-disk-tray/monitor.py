# -*- coding: utf-8 -*-

import time
import subprocess
from PyQt6.QtCore import QObject, pyqtSignal

class YandexDiskMonitor(QObject):
    """Мониторинг Yandex.Disk"""
    status_changed = pyqtSignal(str, str)  # status_code, status_text
    warning = pyqtSignal(str)
    sync_progress = pyqtSignal(str)  # Прогресс синхронизации
    
    def __init__(self):
        super().__init__()
        self.running = True
        self.last_status = None
        self.start_attempts = 0
        self.max_start_attempts = 3
        self.manual_stop = False  # Флаг ручной остановки
        self.force_sync = False   # Флаг принудительной синхронизации
    
    def stop(self):
        self.running = False
    
    def set_manual_stop(self, manual):
        """Устанавливает флаг ручной остановки"""
        self.manual_stop = manual
    
    def force_sync_now(self):
        """Запускает принудительную синхронизацию"""
        self.force_sync = True
        self.warning.emit("🔄 Запущена принудительная синхронизация...")
    
    def check_disk_running(self):
        """Проверяет, запущен ли процесс yandex-disk"""
        try:
            result = subprocess.run(
                ["ps", "aux"],
                capture_output=True,
                text=True
            )
            for line in result.stdout.split('\n'):
                if 'yandex-disk' in line and 'grep' not in line and 'python' not in line:
                    if 'start' in line or 'daemon' in line:
                        return True
            return False
        except Exception as e:
            print(f"Ошибка проверки процесса: {e}")
            return False
    
    def start_disk(self):
        """Запускает yandex-disk"""
        try:
            subprocess.Popen(["yandex-disk", "start"], 
                           stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL)
            return True
        except Exception as e:
            print(f"Ошибка запуска: {e}")
            return False
    
    def stop_disk(self):
        """Останавливает yandex-disk"""
        try:
            subprocess.run(["yandex-disk", "stop"], 
                         stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL)
            return True
        except Exception as e:
            print(f"Ошибка остановки: {e}")
            return False
    
    def sync_disk(self):
        """Принудительная синхронизация"""
        try:
            subprocess.Popen(["yandex-disk", "sync"], 
                           stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL)
            return True
        except Exception as e:
            print(f"Ошибка синхронизации: {e}")
            return False
    
    def get_status(self):
        """Получает статус yandex-disk (русская версия)"""
        try:
            result = subprocess.run(
                ["yandex-disk", "status"],
                capture_output=True,
                text=True,
                timeout=5
            )
            output = result.stdout.strip()
            
            # Проверяем статус по ключевым словам
            if "Статус ядра синхронизации:" in output:
                # Извлекаем статус из строки
                for line in output.split('\n'):
                    if "Статус ядра синхронизации:" in line:
                        if "ожидание команды" in line:
                            return "waiting", "🟡 Ожидание"
                        elif "синхронизация" in line:
                            return "running", "🟢 Синхронизация"
                        else:
                            return "running", "🟢 Работает"
                return "running", "🟢 Синхронизация"
            elif "Path to the sync folder:" in output:
                return "running", "🟢 Синхронизация"
            else:
                return "stopped", "🔴 Остановлен"
                
        except subprocess.TimeoutExpired:
            return "timeout", "⏰ Таймаут"
        except FileNotFoundError:
            return "error", "⚠️ yandex-disk не установлен"
        except Exception as e:
            return "error", f"⚠️ Ошибка: {str(e)[:30]}"
    
    def get_disk_usage(self):
        """Получает информацию о диске из статуса"""
        try:
            result = subprocess.run(
                ["yandex-disk", "status"],
                capture_output=True,
                text=True,
                timeout=5
            )
            output = result.stdout
            
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
        except:
            return ""
    
    def run(self):
        """Основной цикл мониторинга"""
        start_time = None
        warning_shown = False
        last_status = None
        last_sync_time = 0
        
        while self.running:
            try:
                # Проверяем запущен ли процесс
                process_running = self.check_disk_running()
                
                # Если процесс не запущен
                if not process_running:
                    # Если это не ручная остановка - запускаем
                    if not self.manual_stop:
                        if start_time is None:
                            self.warning.emit("❌ Yandex.Disk не запущен! Запускаю...")
                            self.start_disk()
                            start_time = time.time()
                            warning_shown = False
                    else:
                        # Ручная остановка - просто ждём
                        start_time = None
                    time.sleep(2)
                    continue
                else:
                    # Процесс запущен, сбрасываем флаг ручной остановки
                    if self.manual_stop:
                        self.manual_stop = False
                    # Сбрасываем таймер
                    if start_time is not None:
                        start_time = None
                        warning_shown = False
                
                # Получаем статус
                status_code, status_text = self.get_status()
                
                # Принудительная синхронизация
                if self.force_sync:
                    if status_code == "running" or status_code == "waiting":
                        self.sync_disk()
                        self.sync_progress.emit("🔄 Принудительная синхронизация запущена")
                    else:
                        self.warning.emit("⚠️ Невозможно запустить синхронизацию: диск не активен")
                    self.force_sync = False
                
                # Проверяем таймаут запуска (только если не ручная остановка)
                if status_code != "running" and start_time is not None and not self.manual_stop:
                    elapsed = time.time() - start_time
                    if elapsed > 5 and not warning_shown:
                        self.warning.emit(
                            f"⚠️ Yandex.Disk не запускается более 5 секунд!\n"
                            f"Текущий статус: {status_text}"
                        )
                        warning_shown = True
                        self.start_attempts += 1
                        
                        if self.start_attempts >= self.max_start_attempts:
                            self.warning.emit("🔄 Перезапускаю Yandex.Disk...")
                            self.stop_disk()
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