import requests
import re
import json
import os
import subprocess
from pathlib import Path
from PyQt5.QtCore import QThread, pyqtSignal
import shutil
import psutil
import time

from utils import extract_video_id, sanitize_filename, format_size
from config import Config

class VideoDownloader(QThread):
    """Поток для скачивания видео"""
    
    progress_updated = pyqtSignal(str, int, int)
    status_updated = pyqtSignal(str, str)
    conversion_progress = pyqtSignal(str, int)
    conversion_log = pyqtSignal(str, str)
    download_finished = pyqtSignal(str, bool, str)
    info_received = pyqtSignal(object)
    ffmpeg_check = pyqtSignal(bool, str)
    
    def __init__(self):
        super().__init__()
        self.download_queue = []
        self.current_video = None
        self.is_running = False
        self.ffmpeg_path = self.find_ffmpeg()
        self.session = requests.Session()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'Referer': 'https://rutube.ru/'
        }
        self.session.headers.update(self.headers)
        self.check_ffmpeg()
    
    def find_ffmpeg(self):
        """Ищет ffmpeg в системе"""
        ffmpeg_path = shutil.which('ffmpeg')
        if ffmpeg_path:
            return ffmpeg_path
        
        common_paths = [
            '/usr/local/bin/ffmpeg',
            '/usr/bin/ffmpeg'
        ]
        
        for path in common_paths:
            if os.path.exists(path):
                return path
        return None
    
    def check_ffmpeg(self):
        """Проверяет доступность ffmpeg"""
        if not self.ffmpeg_path:
            self.ffmpeg_check.emit(False, "FFmpeg не найден")
            return
        
        try:
            result = subprocess.run(
                [self.ffmpeg_path, '-version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                version_line = result.stdout.split('\n')[0]
                version = version_line.split('version')[1].split()[0] if 'version' in version_line else 'unknown'
                self.ffmpeg_check.emit(True, version)
            else:
                self.ffmpeg_check.emit(False, "Ошибка выполнения")
        except Exception as e:
            self.ffmpeg_check.emit(False, str(e))
    
    def add_to_queue(self, video_info, download_path, quality=None, conversion_settings=None):
        """Добавляет видео в очередь"""
        video_info.download_path = download_path
        video_info.conversion_settings = conversion_settings or {}
        
        if quality and quality in video_info.qualities:
            video_info.selected_quality = quality
            print(f"[DEBUG] Выбрано качество: {quality}")
        elif video_info.qualities:
            def get_quality_number(q):
                numbers = re.findall(r'\d+', q)
                return int(numbers[0]) if numbers else 0
            qualities = sorted(video_info.qualities.keys(), key=get_quality_number, reverse=True)
            video_info.selected_quality = qualities[0] if qualities else None
            print(f"[DEBUG] Автовыбор качества: {video_info.selected_quality}")
        
        self.download_queue.append(video_info)
    
    def run(self):
        """Запускает обработку очереди"""
        self.is_running = True
        
        for video_info in self.download_queue:
            if not self.is_running:
                break
            
            self.current_video = video_info
            success, message, output_path = self.download_and_convert(video_info)
            self.download_finished.emit(video_info.video_id, success, 
                                       f"{message}|{output_path}" if output_path else message)
        
        self.is_running = False
        self.current_video = None
    
    def stop(self):
        """Останавливает скачивание"""
        self.is_running = False
    
    def get_video_info(self, url):
        """Получает информацию о видео по URL с принудительным парсингом качеств"""
        try:
            video_id = extract_video_id(url)
            if not video_id:
                print(f"[ERROR] Не удалось извлечь ID из URL: {url}")
                return None
            
            print(f"[DEBUG] Получение информации для видео ID: {video_id}")
            
            # Основной API
            api_url = f"https://rutube.ru/api/play/options/{video_id}/"
            response = self.session.get(api_url, timeout=10)
            
            if response.status_code != 200:
                print(f"[ERROR] API вернул код {response.status_code}")
                return None
            
            api_data = response.json()
            
            # Метаданные видео
            meta_url = f"https://rutube.ru/api/video/{video_id}/"
            meta_response = self.session.get(meta_url, timeout=10)
            meta_data = {}
            if meta_response.status_code == 200:
                meta_data = meta_response.json()
            
            title = meta_data.get('title', api_data.get('title', 'Без названия'))
            description = meta_data.get('description', '')
            duration = meta_data.get('duration', 0)
            
            print(f"[DEBUG] Название: {title}")
            print(f"[DEBUG] Длительность: {duration}")
            
            # ПРИНУДИТЕЛЬНЫЙ ПАРСИНГ КАЧЕСТВ
            qualities = {}
            
            # 1. Пробуем получить из video_balancer
            if 'video_balancer' in api_data:
                video_balancer = api_data['video_balancer']
                
                # Прямые ссылки на MP4
                if 'mp4' in video_balancer:
                    for quality, url in video_balancer['mp4'].items():
                        if isinstance(quality, (int, float)):
                            quality = f"{quality}p"
                        elif isinstance(quality, str) and quality.isdigit():
                            quality = f"{quality}p"
                        qualities[quality] = url
                        print(f"[DEBUG] Найдено качество {quality}")
                
                # Если нет mp4, пробуем m3u8
                if not qualities and 'm3u8' in video_balancer:
                    qualities['HLS'] = video_balancer['m3u8']
                    print("[DEBUG] Найден HLS поток")
            
            # 2. Альтернативный API
            if not qualities:
                alt_api_url = f"https://rutube.ru/api/video/{video_id}/play/"
                alt_response = self.session.get(alt_api_url, timeout=10)
                if alt_response.status_code == 200:
                    alt_data = alt_response.json()
                    if 'video_balancer' in alt_data:
                        video_balancer = alt_data['video_balancer']
                        if 'mp4' in video_balancer:
                            for quality, url in video_balancer['mp4'].items():
                                if isinstance(quality, (int, float)):
                                    quality = f"{quality}p"
                                elif isinstance(quality, str) and quality.isdigit():
                                    quality = f"{quality}p"
                                qualities[quality] = url
                                print(f"[DEBUG] Найдено качество {quality} (альт. API)")
            
            # 3. Парсим HTML страницы
            if not qualities:
                print("[DEBUG] Пробуем спарсить качества из HTML...")
                video_url = f"https://rutube.ru/video/{video_id}/"
                html_response = self.session.get(video_url, timeout=10)
                if html_response.status_code == 200:
                    html = html_response.text
                    
                    # Ищем JSON с данными в HTML
                    json_pattern = r'<script type="application/ld\+json">(.*?)</script>'
                    json_matches = re.findall(json_pattern, html, re.DOTALL)
                    
                    for json_str in json_matches:
                        try:
                            data = json.loads(json_str)
                            if data.get('@type') == 'VideoObject':
                                if 'contentUrl' in data:
                                    qualities['Original'] = data['contentUrl']
                                    print("[DEBUG] Найдена прямая ссылка из JSON-LD")
                        except:
                            pass
                    
                    # Ищем в JavaScript переменных
                    js_patterns = [
                        r'video_url["\']?\s*[:=]\s*["\']([^"\']+\.mp4[^"\']*)',
                        r'url["\']?\s*[:=]\s*["\']([^"\']+\.mp4[^"\']*)',
                        r'src["\']?\s*[:=]\s*["\']([^"\']+\.mp4[^"\']*)'
                    ]
                    
                    for pattern in js_patterns:
                        matches = re.findall(pattern, html)
                        for match in matches:
                            # Очищаем ссылку
                            clean_url = match.replace('\\/', '/')
                            qualities['Unknown'] = clean_url
                            print(f"[DEBUG] Найдена ссылка: {clean_url[:50]}...")
            
            # 4. Если все еще нет качеств, создаем тестовые для отладки
            if not qualities:
                print("[WARNING] Не найдено ни одного качества!")
                # Пробуем собрать из доступных данных
                if 'video_balancer' in api_data:
                    if 'hls' in api_data['video_balancer']:
                        qualities['HLS'] = api_data['video_balancer']['hls']
                    if 'default' in api_data['video_balancer']:
                        qualities['Default'] = api_data['video_balancer']['default']
            
            print(f"[DEBUG] Всего найдено качеств: {len(qualities)}")
            for q in qualities.keys():
                print(f"  - {q}")
            
            from utils import VideoInfo
            video_info = VideoInfo(
                url=url,
                video_id=video_id,
                title=title,
                duration=duration,
                description=description,
                qualities=qualities
            )
            
            return video_info
            
        except Exception as e:
            print(f"[ERROR] Ошибка получения информации: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def download_and_convert(self, video_info):
        """Скачивает и конвертирует видео"""
        try:
            if not hasattr(video_info, 'selected_quality') or not video_info.selected_quality:
                print("[ERROR] Не выбрано качество видео")
                if video_info.qualities:
                    def get_quality_number(q):
                        numbers = re.findall(r'\d+', q)
                        return int(numbers[0]) if numbers else 0
                    qualities = sorted(video_info.qualities.keys(), key=get_quality_number, reverse=True)
                    video_info.selected_quality = qualities[0] if qualities else None
                    print(f"[DEBUG] Принудительный выбор: {video_info.selected_quality}")
                else:
                    return False, "Нет доступных качеств видео", None
            
            if video_info.selected_quality not in video_info.qualities:
                print(f"[ERROR] Качество {video_info.selected_quality} недоступно")
                print(f"Доступные: {list(video_info.qualities.keys())}")
                return False, f"Качество {video_info.selected_quality} недоступно", None
            
            video_url = video_info.qualities[video_info.selected_quality]
            print(f"[DEBUG] URL видео: {video_url[:100]}...")
            print(f"[DEBUG] Выбранное качество: {video_info.selected_quality}")
            
            safe_title = sanitize_filename(video_info.title)
            
            output_dir = Path(video_info.download_path)
            output_dir.mkdir(parents=True, exist_ok=True)
            
            conv_settings = video_info.conversion_settings or {}
            
            if conv_settings and conv_settings.get('enabled', False):
                codec = conv_settings.get('codec', 'H264')
                if codec in ['AAC', 'MP3']:
                    ext = '.m4a' if codec == 'AAC' else '.mp3'
                else:
                    ext = '.mp4'
            else:
                ext = '.mp4'
            
            counter = 1
            output_file = output_dir / f"{safe_title}{ext}"
            while output_file.exists():
                output_file = output_dir / f"{safe_title}_{counter}{ext}"
                counter += 1
            
            print(f"[DEBUG] Выходной файл: {output_file}")
            
            if conv_settings and conv_settings.get('enabled', False):
                cmd = self.build_ffmpeg_command(video_url, str(output_file), video_info, conv_settings)
                status_message = "Конвертация"
                print("[DEBUG] Режим: конвертация")
            else:
                cmd = [
                    self.ffmpeg_path, '-y',
                    '-headers', f'User-Agent: {self.headers["User-Agent"]}\r\nReferer: {self.headers["Referer"]}\r\n',
                    '-i', video_url,
                    '-c', 'copy',
                    '-bsf:a', 'aac_adtstoasc',
                    str(output_file)
                ]
                status_message = "Скачивание"
                print("[DEBUG] Режим: копирование")
            
            print(f"[DEBUG] Запуск FFmpeg: {' '.join(cmd)}")
            self.status_updated.emit(video_info.video_id, status_message)
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                bufsize=1
            )
            
            duration = None
            stderr_output = []
            
            while self.is_running:
                line = process.stderr.readline()
                if not line and process.poll() is not None:
                    break
                
                if line:
                    stderr_output.append(line)
                    print(f"[FFmpeg] {line.strip()}")
                    
                    if 'Duration' in line and not duration:
                        match = re.search(r'Duration: (\d{2}):(\d{2}):(\d{2})\.\d+', line)
                        if match:
                            h, m, s = map(int, match.groups())
                            duration = h * 3600 + m * 60 + s
                            print(f"[DEBUG] Длительность видео: {duration} сек")
                    
                    if 'time=' in line and duration:
                        match = re.search(r'time=(\d{2}):(\d{2}):(\d{2})\.\d+', line)
                        if match:
                            h, m, s = map(int, match.groups())
                            current_time = h * 3600 + m * 60 + s
                            if duration > 0:
                                progress = int((current_time / duration) * 100)
                                progress = min(progress, 99)
                                self.conversion_progress.emit(video_info.video_id, progress)
                    
                    self.conversion_log.emit(video_info.video_id, line.strip())
            
            process.wait()
            
            if process.returncode == 0 and os.path.exists(output_file):
                file_size = os.path.getsize(output_file)
                if file_size > 0:
                    self.conversion_progress.emit(video_info.video_id, 100)
                    print(f"[DEBUG] Готово: {output_file} ({file_size} байт)")
                    return True, "Готово", str(output_file)
                else:
                    return False, "Выходной файл пуст", None
            else:
                error_output = '\n'.join(stderr_output[-20:])
                print(f"[ERROR] FFmpeg error (code {process.returncode})")
                return False, f"Ошибка FFmpeg (код {process.returncode})", None
            
        except Exception as e:
            print(f"[ERROR] Exception: {str(e)}")
            import traceback
            traceback.print_exc()
            return False, f"Ошибка: {str(e)}", None
    
    def build_ffmpeg_command(self, input_url, output_file, video_info, settings):
        """Строит команду FFmpeg"""
        cmd = [self.ffmpeg_path, '-y', '-i', input_url]
        cmd.extend(['-headers', f'User-Agent: {self.headers["User-Agent"]}\r\nReferer: {self.headers["Referer"]}\r\n'])
        
        codec = settings.get('codec', 'H264')
        
        if codec in ['AAC', 'MP3']:
            cmd.extend(['-vn'])
            if codec == 'AAC':
                cmd.extend(['-c:a', 'aac'])
            else:
                cmd.extend(['-c:a', 'libmp3lame'])
            
            audio_bitrate = settings.get('audio_bitrate', 192)
            if audio_bitrate != 'auto':
                cmd.extend(['-b:a', f'{audio_bitrate}k'])
        else:
            video_codecs = {
                'H264': 'libx264',
                'H265': 'libx265',
                'VP9': 'libvpx-vp9'
            }
            video_encoder = video_codecs.get(codec, 'libx264')
            cmd.extend(['-c:v', video_encoder])
            
            resolution = settings.get('resolution', 'Original')
            if resolution != 'Original':
                for res in Config.AVAILABLE_RESOLUTIONS:
                    if res['name'] == resolution and res['width'] and res['height']:
                        cmd.extend(['-vf', f'scale={res["width"]}:{res["height"]}'])
                        break
            
            video_bitrate = settings.get('video_bitrate', 'auto')
            if video_bitrate != 'auto':
                cmd.extend(['-b:v', f'{video_bitrate}k'])
            
            if video_encoder in ['libx264', 'libx265']:
                preset = settings.get('preset', 'medium')
                cmd.extend(['-preset', preset])
            
            cmd.extend(['-crf', '23'])
            cmd.extend(['-c:a', 'aac'])
            
            audio_bitrate = settings.get('audio_bitrate', 192)
            if audio_bitrate != 'auto':
                cmd.extend(['-b:a', f'{audio_bitrate}k'])
        
        cmd.extend([
            '-metadata', f'title={video_info.title}',
            '-metadata', 'artist=Rutube Downloader',
            '-movflags', '+faststart',
            output_file
        ])
        
        return cmd