import re
import requests
from urllib.parse import urlparse
import json
from datetime import timedelta

class VideoInfo:
    """Класс для хранения информации о видео"""
    def __init__(self, url, video_id, title, duration, description, qualities):
        self.url = url
        self.video_id = video_id
        self.title = title
        self.duration = duration
        self.description = description
        self.qualities = qualities  # Словарь {quality: url}
        self.selected_quality = None
        self.status = "Ожидание"
        self.progress = 0
        self.download_path = None

def extract_video_id(url):
    """Извлекает ID видео из URL Rutube"""
    patterns = [
        r'/video/([a-f0-9]+)/?',
        r'/video/([a-f0-9]+)\?',
        r'/video/private/([a-f0-9]+)/?'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def format_duration(seconds):
    """Форматирует длительность в читаемый вид"""
    if not seconds:
        return "00:00"
    
    try:
        seconds = int(seconds)
        td = timedelta(seconds=seconds)
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes:02d}:{secs:02d}"
    except:
        return "00:00"

def format_size(bytes):
    """Форматирует размер файла"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes < 1024.0:
            return f"{bytes:.1f} {unit}"
        bytes /= 1024.0
    return f"{bytes:.1f} TB"

def sanitize_filename(filename):
    """Очищает имя файла от недопустимых символов"""
    # Заменяем недопустимые символы на подчеркивание
    filename = re.sub(r'[\\/*?:"<>|]', '_', filename)
    # Убираем лишние пробелы
    filename = ' '.join(filename.split())
    # Ограничиваем длину
    if len(filename) > 200:
        filename = filename[:200]
    return filename