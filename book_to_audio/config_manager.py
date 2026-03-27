import json
import os
from pathlib import Path

class ConfigManager:
    """Управление сохранением и загрузкой конфигурации"""
    
    CONFIG_FILE = "config.json"
    
    def __init__(self):
        self.config = {
            "work_dir": "",
            "last_step": 0,
            "accent_model": "turbo",
            "language": "ru",
            "window_geometry": "900x700",
            "auto_save": True,
            "voice": "aidar_v2",           # Голос
            "speed": 1.0,               # Скорость речи
            "output_format": "mp3"      # Формат: mp3 или wav
        }
        self.load()
    
    def save(self):
        """Сохранить конфигурацию в файл"""
        try:
            with open(self.CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"Ошибка сохранения конфигурации: {e}")
            return False
    
    def load(self):
        """Загрузить конфигурацию из файла"""
        if os.path.exists(self.CONFIG_FILE):
            try:
                with open(self.CONFIG_FILE, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    self.config.update(loaded)
            except Exception as e:
                print(f"Ошибка загрузки конфигурации: {e}")
    
    def get(self, key, default=None):
        """Получить значение по ключу"""
        return self.config.get(key, default)
    
    def set(self, key, value):
        """Установить значение и сохранить"""
        self.config[key] = value
        if self.config.get("auto_save", True):
            self.save()
    
    def get_work_subdirs(self):
        """Создать и получить пути к подкаталогам"""
        work_dir = self.config.get("work_dir")
        if not work_dir or not os.path.exists(work_dir):
            return None
        
        work_path = Path(work_dir)
        
        # Создаём вложенные каталоги
        dirs = {
            "extracted": work_path / "01_extracted_text",
            "accented": work_path / "02_accented_text", 
            "audio": work_path / "03_audio"
        }
        
        for dir_path in dirs.values():
            dir_path.mkdir(exist_ok=True)
        
        return dirs
