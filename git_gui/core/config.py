# core/config.py
import json
import os
from pathlib import Path
from typing import Optional

class Config:
    """Управление настройками приложения"""
    
    CONFIG_DIR = Path.home() / ".git_gui"
    CONFIG_FILE = CONFIG_DIR / "config.json"
    
    @classmethod
    def _ensure_config_dir(cls):
        """Создать директорию для конфигурации если её нет"""
        cls.CONFIG_DIR.mkdir(exist_ok=True)
    
    @classmethod
    def get_last_repo(cls) -> Optional[str]:
        """Получить путь к последнему репозиторию"""
        cls._ensure_config_dir()
        
        if not cls.CONFIG_FILE.exists():
            return None
        
        try:
            with open(cls.CONFIG_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                last_repo = data.get('last_repository')
                
                # Проверяем, существует ли репозиторий
                if last_repo and os.path.exists(last_repo):
                    return last_repo
                return None
        except Exception:
            return None
    
    @classmethod
    def save_last_repo(cls, repo_path: str):
        """Сохранить путь к последнему репозиторию"""
        cls._ensure_config_dir()
        
        try:
            data = {}
            if cls.CONFIG_FILE.exists():
                with open(cls.CONFIG_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            
            data['last_repository'] = repo_path
            
            with open(cls.CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Ошибка сохранения настроек: {e}")