import os
from pathlib import Path
from ruaccent import RUAccent
import time

class AccentProcessor:
    """Расстановка ударений в тексте"""
    
    def __init__(self, work_dir, model_size='turbo'):
        self.work_dir = Path(work_dir)
        self.accented_dir = self.work_dir / "02_accented_text"
        self.accented_dir.mkdir(exist_ok=True)
        
        # Инициализация модели ударений
        self.accentizer = RUAccent()
        print(f"Загрузка модели ударений ({model_size})...")
        
        # Список моделей для попыток
        models_to_try = [model_size, 'turbo', 'tiny']
        loaded = False
        
        for model in models_to_try:
            try:
                self.accentizer.load(
                    omograph_model_size=model,
                    use_dictionary=True
                )
                print(f"Модель {model} загружена успешно")
                self.model_size = model
                loaded = True
                break
            except Exception as e:
                print(f"Модель {model} не загрузилась: {e}")
                continue
        
        if not loaded:
            print("ВНИМАНИЕ: Не удалось загрузить модель ударений. Будет использован оригинальный текст без изменений.")
            self.model_loaded = False
        else:
            self.model_loaded = True
    
    def process_file(self, input_file):
        """Обработка файла с расстановкой ударений"""
        input_file = Path(input_file)
        
        # Чтение текста
        with open(input_file, 'r', encoding='utf-8') as f:
            text = f.read()
        
        if not text.strip():
            print(f"Пустой файл: {input_file}")
            return None
        
        print(f"Обработка {input_file.name}...")
        start_time = time.time()
        
        # Если модель не загружена, просто копируем текст
        if not self.model_loaded:
            print("  Модель не загружена, копируем без обработки")
            accented_text = text
        else:
            try:
                # Обрабатываем весь текст целиком
                accented_text = self.accentizer.process_all(text)
            except Exception as e:
                print(f"  Ошибка при расстановке ударений: {e}")
                print("  Использую оригинальный текст без ударений")
                accented_text = text
        
        elapsed = time.time() - start_time
        print(f"Обработка завершена за {elapsed:.1f} сек")
        
        # Сохраняем размеченный текст
        output_file = self.accented_dir / f"{input_file.stem}_accented.txt"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(accented_text)
        
        # Сохраняем чистую версию (без ударений) для TTS
        clean_text = accented_text.replace('+', '')
        clean_file = self.accented_dir / f"{input_file.stem}_clean.txt"
        with open(clean_file, 'w', encoding='utf-8') as f:
            f.write(clean_text)
        
        return output_file
    
    def process_all(self):
        """Обработать все извлечённые файлы"""
        extracted_dir = self.work_dir / "01_extracted_text"
        if not extracted_dir.exists():
            print("Папка с извлечёнными текстами не найдена")
            return []
        
        results = []
        txt_files = list(extracted_dir.glob("*.txt"))
        print(f"Найдено файлов для обработки: {len(txt_files)}")
        
        for i, txt_file in enumerate(txt_files, 1):
            print(f"\n--- Файл {i}/{len(txt_files)}: {txt_file.name} ---")
            try:
                result = self.process_file(txt_file)
                if result:
                    results.append(result)
                    print(f"  Сохранено: {result.name}")
            except Exception as e:
                print(f"  Ошибка обработки {txt_file}: {e}")
        
        return results
    
    def get_accented_files(self):
        """Получить список обработанных файлов"""
        return list(self.accented_dir.glob("*.txt"))