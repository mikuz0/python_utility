import torch
import numpy as np
from pathlib import Path
import time
import warnings
import subprocess
import tempfile
import os
warnings.filterwarnings("ignore", category=UserWarning)

# Используем scipy для сохранения WAV
from scipy.io.wavfile import write as write_wav

class AudioGenerator:
    """Генерация аудио через Silero"""
    
    # Доступные голоса для русского языка
    AVAILABLE_VOICES = {
        'aidar_v2': 'Мужской (aidar)',
        'baya_v2': 'Женский (baya)',
        'kseniya_v2': 'Женский (kseniya)',
        'natasha_v2': 'Женский (natasha)',
        'ruslan_v2': 'Мужской (ruslan)',
        'irina_v2': 'Женский (irina)'
    }
    
    def __init__(self, work_dir, language='ru', voice='aidar_v2', speed=1.0, output_format='mp3'):
        self.work_dir = Path(work_dir)
        self.audio_dir = self.work_dir / "03_audio"
        self.audio_dir.mkdir(exist_ok=True)
        
        # Проверяем корректность голоса
        if voice not in self.AVAILABLE_VOICES:
            print(f"Предупреждение: голос '{voice}' не найден. Используем 'aidar_v2'")
            voice = 'aidar_v2'
        
        self.voice = voice
        self.speed = speed
        self.output_format = output_format.lower()
        self.language = language
        
        print(f"Загрузка Silero модели...")
        print(f"  Голос: {voice} ({self.AVAILABLE_VOICES.get(voice, voice)})")
        print(f"  Формат: {self.output_format.upper()}")
        print(f"  Примечание: скорость речи настраивается через sample_rate")
        
        self.device = torch.device('cpu')
        
        try:
            # Загружаем модель для русского языка
            self.model, self.model_sample_rate = torch.hub.load(
                repo_or_dir='snakers4/silero-models',
                model='silero_tts',
                language=language,
                speaker=voice,
                trust_repo=True
            )
            self.model.to(self.device)
            print(f"Модель загружена успешно")
        except Exception as e:
            print(f"Ошибка загрузки модели: {e}")
            raise
    
    def save_audio(self, audio_tensor, output_path, sample_rate=24000):
        """Сохранить аудио тензор в файл (WAV или MP3)"""
        # Преобразуем тензор в numpy
        audio_np = audio_tensor.cpu().numpy()
        
        # Нормализуем к диапазону int16
        if np.max(np.abs(audio_np)) > 0:
            audio_np = audio_np / np.max(np.abs(audio_np))
        audio_int16 = (audio_np * 32767).astype(np.int16)
        
        # Если нужен WAV, сохраняем напрямую
        if self.output_format == 'wav':
            write_wav(str(output_path), sample_rate, audio_int16)
            print(f"  Сохранено как WAV")
            return output_path
        
        # Если нужен MP3, сначала сохраняем во временный WAV, затем конвертируем
        if self.output_format == 'mp3':
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
                tmp_wav = tmp.name
            
            try:
                # Сохраняем временный WAV
                write_wav(tmp_wav, sample_rate, audio_int16)
                
                # Конвертируем в MP3 через ffmpeg
                mp3_path = output_path.with_suffix('.mp3')
                cmd = [
                    'ffmpeg', '-y', '-i', tmp_wav,
                    '-b:a', '192k',
                    '-ar', str(sample_rate),
                    str(mp3_path)
                ]
                subprocess.run(cmd, capture_output=True, check=True)
                print(f"  Сохранено как MP3")
                return mp3_path
            finally:
                if os.path.exists(tmp_wav):
                    os.unlink(tmp_wav)
        
        return output_path
    
    def generate(self, text_file, language='ru'):
        """Генерация аудио из текстового файла"""
        text_file = Path(text_file)
        
        with open(text_file, 'r', encoding='utf-8') as f:
            text = f.read()
        
        # Очищаем текст
        text = text.replace('+', '')
        text = text.replace('\n', ' ').strip()
        
        if not text or len(text) < 10:
            print(f"Текст слишком короткий или пустой: {text_file}")
            return None
        
        print(f"Генерация аудио для {text_file.name}...")
        start_time = time.time()
        
        # Разбиваем на предложения
        clean_text = text.replace('!', '.').replace('?', '.').replace('...', '.')
        sentences = [s.strip() for s in clean_text.split('.') if len(s.strip()) > 10]
        
        if not sentences:
            sentences = [s.strip() for s in text.split('\n') if len(s.strip()) > 10]
        
        if not sentences:
            sentences = [text[:500]]
        
        print(f"Разбито на {len(sentences)} предложений")
        
        audio_parts = []
        # sample_rate влияет на скорость речи: ниже = медленнее, выше = быстрее
        # 16000 - нормальная скорость, 24000 - быстрее, 12000 - медленнее
        base_rate = 16000
        target_sample_rate = int(base_rate * self.speed)
        
        for i, sent in enumerate(sentences):
            if not sent:
                continue
            print(f"  Обработка предложения {i+1}/{len(sentences)} ({len(sent)} символов)")
            
            try:
                # Правильный вызов API: только texts и sample_rate
                result = self.model.apply_tts(
                    texts=sent,
                    sample_rate=target_sample_rate
                )
                
                # result - это список из одного тензора
                if isinstance(result, list) and len(result) > 0:
                    audio_parts.append(result[0])
                else:
                    audio_parts.append(result)
                    
            except Exception as e:
                print(f"  Ошибка: {e}")
                continue
        
        if not audio_parts:
            raise Exception("Не удалось сгенерировать аудио")
        
        # Объединяем все части
        final_audio = torch.cat(audio_parts)
        
        output_name = text_file.stem.replace('_accented', '').replace('_clean', '').replace('_extracted', '')
        extension = '.mp3' if self.output_format == 'mp3' else '.wav'
        output_file = self.audio_dir / f"{output_name}{extension}"
        self.save_audio(final_audio, output_file, target_sample_rate)
        
        elapsed = time.time() - start_time
        print(f"Генерация завершена за {elapsed:.1f} сек")
        
        return output_file
    
    def generate_all(self, language='ru'):
        """Сгенерировать аудио для всех обработанных текстов"""
        accented_dir = self.work_dir / "02_accented_text"
        if not accented_dir.exists():
            print("Папка с текстами с ударениями не найдена")
            return []
        
        results = []
        # Используем clean файлы (без ударений)
        txt_files = list(accented_dir.glob("*_clean.txt"))
        if not txt_files:
            txt_files = list(accented_dir.glob("*.txt"))
        
        print(f"Найдено файлов для обработки: {len(txt_files)}")
        
        for i, txt_file in enumerate(txt_files, 1):
            print(f"\n--- Файл {i}/{len(txt_files)}: {txt_file.name} ---")
            try:
                result = self.generate(txt_file, language)
                if result:
                    results.append(result)
                    print(f"  Сохранено: {result.name}")
            except Exception as e:
                print(f"  Ошибка генерации {txt_file}: {e}")
        
        return results
    
    def get_audio_files(self):
        """Получить список сгенерированных аудиофайлов"""
        extension = '.mp3' if self.output_format == 'mp3' else '.wav'
        return list(self.audio_dir.glob(f"*{extension}"))