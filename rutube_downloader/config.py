import json
import os
from pathlib import Path

class Config:
    """Класс для работы с настройками приложения"""
    
    CONFIG_FILE = Path.home() / '.rutube_downloader_config.json'
    
    # Доступные кодеки и параметры
    AVAILABLE_CODECS = {
        'H264': {
            'name': 'H.264',
            'pixel_formats': ['yuv420p', 'yuv422p', 'yuv444p'],
            'presets': ['ultrafast', 'superfast', 'veryfast', 'faster', 'fast', 'medium', 'slow', 'slower', 'veryslow'],
            'profiles': ['baseline', 'main', 'high']
        },
        'H265': {
            'name': 'H.265/HEVC',
            'pixel_formats': ['yuv420p', 'yuv422p', 'yuv444p'],
            'presets': ['ultrafast', 'superfast', 'veryfast', 'faster', 'fast', 'medium', 'slow', 'slower', 'veryslow'],
            'profiles': ['main', 'main10', 'main12']
        },
        'VP9': {
            'name': 'VP9',
            'pixel_formats': ['yuv420p', 'yuv422p', 'yuv444p'],
            'profiles': ['profile0', 'profile1', 'profile2', 'profile3']
        },
        'AAC': {
            'name': 'AAC Audio only',
            'is_audio_only': True,
            'profiles': ['LC', 'HE', 'HEv2'],
            'sample_rates': [8000, 11025, 16000, 22050, 32000, 44100, 48000]
        },
        'MP3': {
            'name': 'MP3 Audio only',
            'is_audio_only': True,
            'profiles': ['standard'],
            'sample_rates': [8000, 11025, 16000, 22050, 32000, 44100, 48000]
        }
    }
    
    # Доступные разрешения
    AVAILABLE_RESOLUTIONS = [
        {'width': 256, 'height': 144, 'name': '144p'},
        {'width': 426, 'height': 240, 'name': '240p'},
        {'width': 640, 'height': 360, 'name': '360p'},
        {'width': 854, 'height': 480, 'name': '480p'},
        {'width': 1280, 'height': 720, 'name': '720p'},
        {'width': 1920, 'height': 1080, 'name': '1080p'},
        {'width': 2560, 'height': 1440, 'name': '1440p'},
        {'width': 3840, 'height': 2160, 'name': '4K'},
        {'width': None, 'height': None, 'name': 'Original'}
    ]
    
    # Доступные битрейты (в kbps)
    AVAILABLE_BITRATES = {
        '144p': [100, 200, 300, 400, 500],
        '240p': [200, 300, 400, 500, 600, 700],
        '360p': [300, 400, 500, 600, 800, 1000],
        '480p': [500, 700, 1000, 1200, 1500, 2000],
        '720p': [1000, 1500, 2000, 2500, 3000, 4000],
        '1080p': [2000, 3000, 4000, 5000, 6000, 8000],
        '1440p': [4000, 6000, 8000, 10000, 12000, 16000],
        '4K': [8000, 12000, 16000, 20000, 25000, 35000],
        'audio': [64, 96, 128, 160, 192, 256, 320]
    }
    
    # Пресеты совместимости
    COMPATIBILITY_PRESETS = {
        'old_tv': {
            'name': '📺 Старый телевизор/DVD',
            'description': 'Для TV, DVD-плееров и очень старых устройств',
            'ref_frames': 1,
            'level': 'auto_min',
            'maxrate_factor': 1.5,
            'gop_seconds': 2,
            'no_b_frames': True,
            'profile': 'high'
        },
        'old_phone': {
            'name': '📱 Старый смартфон/планшет',
            'description': 'Для Android/iOS 5-8 лет',
            'ref_frames': 2,
            'level': 'auto',
            'maxrate_factor': 2.0,
            'gop_seconds': 3,
            'no_b_frames': False,
            'profile': 'high'
        },
        'modern': {
            'name': '💻 Современные устройства',
            'description': 'ПК, новые смартфоны, Smart TV',
            'ref_frames': 3,
            'level': 'auto',
            'maxrate_factor': 2.5,
            'gop_seconds': 4,
            'no_b_frames': False,
            'profile': 'high'
        },
        'max_compat': {
            'name': '🛡️ Максимальная совместимость',
            'description': 'Работает везде, но файл больше',
            'ref_frames': 1,
            'level': '21',  # Level 2.1 (минимальный для 480p)
            'maxrate_factor': 1.2,
            'gop_seconds': 1,
            'no_b_frames': True,
            'profile': 'baseline'
        }
    }
    
    @staticmethod
    def load_config():
        """Загружает настройки из файла"""
        default_config = {
            'download_path': str(Path.home() / 'Downloads' / 'Rutube'),
            'auto_open_folder': False,
            'conversion': {
                'enabled': False,
                'codec': 'H264',
                'resolution': 'Original',
                'video_bitrate': 'auto',
                'audio_bitrate': 192,
                'framerate': 'original',
                'preset': 'medium',
                'profile': 'high',
                'pixel_format': 'yuv420p',
                'two_pass': False,
                'hardware_acceleration': 'none',
                'audio_only': False,
                'keep_original': False
            },
            'compatibility': {
                'enabled': False,
                'preset': 'old_tv',
                'ref_frames': 1,
                'level': 'auto_min',
                'maxrate_factor': 1.5,
                'gop_seconds': 2,
                'no_b_frames': True,
                'profile': 'high'
            }
        }
        
        if Config.CONFIG_FILE.exists():
            try:
                with open(Config.CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    # Обновляем существующие ключи
                    for key in default_config:
                        if key not in config:
                            config[key] = default_config[key]
                        elif key == 'conversion' and isinstance(config[key], dict):
                            for subkey in default_config['conversion']:
                                if subkey not in config[key]:
                                    config[key][subkey] = default_config['conversion'][subkey]
                        elif key == 'compatibility' and isinstance(config[key], dict):
                            for subkey in default_config['compatibility']:
                                if subkey not in config[key]:
                                    config[key][subkey] = default_config['compatibility'][subkey]
                    return config
            except:
                return default_config
        else:
            return default_config
    
    @staticmethod
    def save_config(config):
        """Сохраняет настройки в файл"""
        try:
            Config.CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(Config.CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Ошибка сохранения конфига: {e}")
            return False
    
    @staticmethod
    def get_download_path():
        """Возвращает путь для скачивания"""
        config = Config.load_config()
        path = Path(config['download_path'])
        path.mkdir(parents=True, exist_ok=True)
        return str(path)
    
    @staticmethod
    def set_download_path(path):
        """Устанавливает новый путь для скачивания"""
        config = Config.load_config()
        config['download_path'] = str(path)
        Config.save_config(config)
    
    @staticmethod
    def get_conversion_settings():
        """Возвращает настройки конвертации"""
        config = Config.load_config()
        return config.get('conversion', {})
    
    @staticmethod
    def save_conversion_settings(settings):
        """Сохраняет настройки конвертации"""
        config = Config.load_config()
        config['conversion'] = settings
        Config.save_config(config)
    
    @staticmethod
    def get_compatibility_settings():
        """Возвращает настройки совместимости"""
        config = Config.load_config()
        return config.get('compatibility', {})
    
    @staticmethod
    def save_compatibility_settings(settings):
        """Сохраняет настройки совместимости"""
        config = Config.load_config()
        config['compatibility'] = settings
        Config.save_config(config)
    
    @staticmethod
    def get_level_for_resolution(width, height, fps=30):
        """
        Возвращает рекомендуемый уровень H.264 для разрешения
        """
        # Таблица уровней H.264
        levels = {
            '1':    {'max_mbps': 1485,   'max_fs': 99,   'max_dpb': 396},
            '1.1':  {'max_mbps': 3000,   'max_fs': 396,  'max_dpb': 900},
            '1.2':  {'max_mbps': 6000,   'max_fs': 396,  'max_dpb': 2376},
            '1.3':  {'max_mbps': 11880,  'max_fs': 396,  'max_dpb': 2376},
            '2':    {'max_mbps': 11880,  'max_fs': 396,  'max_dpb': 2376},
            '2.1':  {'max_mbps': 19800,  'max_fs': 792,  'max_dpb': 4752},
            '2.2':  {'max_mbps': 20250,  'max_fs': 1620, 'max_dpb': 8100},
            '3':    {'max_mbps': 40500,  'max_fs': 1620, 'max_dpb': 8100},
            '3.1':  {'max_mbps': 108000, 'max_fs': 3600, 'max_dpb': 18000},
            '3.2':  {'max_mbps': 216000, 'max_fs': 5120, 'max_dpb': 20480},
            '4':    {'max_mbps': 245760, 'max_fs': 8192, 'max_dpb': 32768},
            '4.1':  {'max_mbps': 245760, 'max_fs': 8192, 'max_dpb': 32768},
            '4.2':  {'max_mbps': 522240, 'max_fs': 8704, 'max_dpb': 34816},
            '5':    {'max_mbps': 589824, 'max_fs': 22080, 'max_dpb': 110400},
            '5.1':  {'max_mbps': 983040, 'max_fs': 36864, 'max_dpb': 184320},
            '5.2':  {'max_mbps': 2073600, 'max_fs': 36864, 'max_dpb': 184320}
        }
        
        # Вычисляем параметры для нашего видео
        mb_width = (width + 15) // 16
        mb_height = (height + 15) // 16
        mb_per_frame = mb_width * mb_height
        mb_per_second = mb_per_frame * fps
        frame_size = mb_per_frame
        
        # Ищем минимальный подходящий уровень
        selected_level = '5.2'
        for level, limits in levels.items():
            if (mb_per_second <= limits['max_mbps'] and 
                frame_size <= limits['max_fs']):
                selected_level = level
                break
        
        # Преобразуем для ffmpeg (убираем точку)
        return selected_level.replace('.', '')