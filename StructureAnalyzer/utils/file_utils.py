# -*- coding: utf-8 -*-

import os
import hashlib
from typing import List, Optional, Dict
from datetime import datetime

class FileUtils:
    """Утилиты для работы с файлами"""
    
    @staticmethod
    def ensure_directory(path: str) -> bool:
        """Создание директории, если она не существует"""
        try:
            os.makedirs(path, exist_ok=True)
            return True
        except OSError as e:
            print(f"Ошибка создания директории {path}: {e}")
            return False
    
    @staticmethod
    def get_file_size(path: str) -> Optional[int]:
        """Получение размера файла в байтах"""
        try:
            return os.path.getsize(path)
        except OSError:
            return None
    
    @staticmethod
    def get_file_info(path: str) -> Dict:
        """Получение подробной информации о файле"""
        info = {
            'exists': False,
            'size': None,
            'modified': None,
            'created': None,
            'extension': None
        }
        
        try:
            if os.path.exists(path):
                stat = os.stat(path)
                info['exists'] = True
                info['size'] = stat.st_size
                info['modified'] = datetime.fromtimestamp(stat.st_mtime)
                info['created'] = datetime.fromtimestamp(stat.st_ctime)
                info['extension'] = os.path.splitext(path)[1].lower()
        except OSError:
            pass
            
        return info
    
    @staticmethod
    def is_text_file(path: str, sample_size: int = 1024) -> bool:
        """Проверка, является ли файл текстовым"""
        try:
            with open(path, 'rb') as f:
                sample = f.read(sample_size)
            return not b'\0' in sample
        except:
            return False
    
    @staticmethod
    def read_file_preview(path: str, max_length: int = 500) -> str:
        """Чтение превью файла"""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read(max_length)
                if len(content) == max_length:
                    content += "..."
                return content
        except UnicodeDecodeError:
            try:
                with open(path, 'r', encoding='cp1251') as f:
                    content = f.read(max_length)
                    if len(content) == max_length:
                        content += "..."
                    return content
            except:
                return "[Бинарный файл]"
        except:
            return "Не удалось прочитать файл"
    
    @staticmethod
    def get_file_hash(path: str, algorithm: str = 'md5') -> Optional[str]:
        """Получение хеша файла"""
        try:
            hash_obj = hashlib.new(algorithm)
            with open(path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b''):
                    hash_obj.update(chunk)
            return hash_obj.hexdigest()
        except:
            return None
    
    @staticmethod
    def format_size(size_bytes: int) -> str:
        """Форматирование размера файла"""
        if size_bytes is None:
            return "Неизвестно"
        
        for unit in ['Б', 'КБ', 'МБ', 'ГБ']:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} ТБ"