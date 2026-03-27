import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os
from pathlib import Path
import threading

from config_manager import ConfigManager
from text_extractor import TextExtractor
from accent_processor import AccentProcessor
from audio_generator import AudioGenerator

class BookToAudioGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Книги в аудио - Конвертер")
        
        # Загрузка конфигурации
        self.config = ConfigManager()
        
        # Установка размеров окна
        geometry = self.config.get("window_geometry", "900x700")
        self.root.geometry(geometry)
        
        # Переменные состояния
        self.work_dir = tk.StringVar(value=self.config.get("work_dir", ""))
        self.accent_model = tk.StringVar(value=self.config.get("accent_model", "turbo"))
        self.language = tk.StringVar(value=self.config.get("language", "ru"))
        self.auto_save = tk.BooleanVar(value=self.config.get("auto_save", True))
        
        # Настройки озвучки
        self.voice = tk.StringVar(value=self.config.get("voice", "aidar_v2"))
        self.speed = tk.DoubleVar(value=self.config.get("speed", 1.0))
        self.output_format = tk.StringVar(value=self.config.get("output_format", "mp3"))
        
        # Компоненты обработки
        self.extractor = None
        self.accentor = None
        self.audio_gen = None
        
        self.current_step = self.config.get("last_step", 0)
        
        self.setup_ui()
        self.update_step_status()
        
        # Привязка сохранения при закрытии
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def setup_ui(self):
        """Создание интерфейса"""
        # Основной контейнер
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Настройка весов для растягивания
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # === Панель настроек ===
        settings_frame = ttk.LabelFrame(main_frame, text="Настройки", padding="10")
        settings_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        settings_frame.columnconfigure(1, weight=1)
        
        # Рабочая папка
        ttk.Label(settings_frame, text="Рабочая папка:").grid(row=0, column=0, sticky=tk.W, padx=5)
        ttk.Entry(settings_frame, textvariable=self.work_dir).grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5)
        ttk.Button(settings_frame, text="Обзор...", command=self.browse_work_dir).grid(row=0, column=2, padx=5)
        
        # Разделитель
        ttk.Separator(settings_frame, orient='horizontal').grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        
        # === Настройки озвучки ===
        ttk.Label(settings_frame, text="Настройки озвучки:", font=('TkDefaultFont', 10, 'bold')).grid(row=2, column=0, columnspan=3, sticky=tk.W, pady=(5,10))
        
        # Голос
        ttk.Label(settings_frame, text="Голос:").grid(row=3, column=0, sticky=tk.W, padx=5)
        voice_combo = ttk.Combobox(settings_frame, textvariable=self.voice, 
                                   values=['aidar_v2', 'baya_v2', 'kseniya_v2', 'natasha_v2', 'ruslan_v2', 'irina_v2'],
                                   state='readonly', width=20)
        voice_combo.grid(row=3, column=1, sticky=tk.W, padx=5)
        ttk.Label(settings_frame, text="aidar_v2 - мужской, baya_v2 - женский, kseniya_v2 - женский").grid(row=3, column=2, sticky=tk.W, padx=5)
        
        # Скорость речи
        ttk.Label(settings_frame, text="Скорость речи:").grid(row=4, column=0, sticky=tk.W, padx=5)
        speed_scale = ttk.Scale(settings_frame, from_=0.5, to=2.0, variable=self.speed, orient='horizontal', length=200)
        speed_scale.grid(row=4, column=1, sticky=tk.W, padx=5)
        self.speed_label = ttk.Label(settings_frame, text=f"{self.speed.get():.1f}x")
        self.speed_label.grid(row=4, column=2, sticky=tk.W, padx=5)
        speed_scale.configure(command=lambda x: self.speed_label.configure(text=f"{self.speed.get():.1f}x"))
        
        # Формат выходного файла
        ttk.Label(settings_frame, text="Формат:").grid(row=5, column=0, sticky=tk.W, padx=5)
        format_frame = ttk.Frame(settings_frame)
        format_frame.grid(row=5, column=1, sticky=tk.W, padx=5)
        ttk.Radiobutton(format_frame, text="MP3", variable=self.output_format, value="mp3").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(format_frame, text="WAV", variable=self.output_format, value="wav").pack(side=tk.LEFT, padx=5)
        
        # Разделитель
        ttk.Separator(settings_frame, orient='horizontal').grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        
        # === Настройки ударений ===
        ttk.Label(settings_frame, text="Настройки обработки:", font=('TkDefaultFont', 10, 'bold')).grid(row=7, column=0, columnspan=3, sticky=tk.W, pady=(5,10))
        
        # Модель ударений
        ttk.Label(settings_frame, text="Модель ударений:").grid(row=8, column=0, sticky=tk.W, padx=5)
        accent_combo = ttk.Combobox(settings_frame, textvariable=self.accent_model, 
                                     values=['turbo', 'tiny', 'turbo3.1', 'medium'],
                                     state='readonly', width=20)
        accent_combo.grid(row=8, column=1, sticky=tk.W, padx=5)
        ttk.Label(settings_frame, text="turbo - баланс, tiny - быстрая, medium - точная").grid(row=8, column=2, sticky=tk.W, padx=5)
        
        ttk.Checkbutton(settings_frame, text="Автосохранение настроек", 
                       variable=self.auto_save).grid(row=9, column=0, columnspan=2, sticky=tk.W, padx=5, pady=5)
        
        # === Панель шагов обработки ===
        steps_frame = ttk.LabelFrame(main_frame, text="Этапы обработки", padding="10")
        steps_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        
        # Кнопки этапов
        btn_frame = ttk.Frame(steps_frame)
        btn_frame.grid(row=0, column=0, columnspan=2, pady=5)
        
        self.step1_btn = ttk.Button(btn_frame, text="1. Извлечь текст", 
                                    command=self.run_step1, width=20)
        self.step1_btn.grid(row=0, column=0, padx=5)
        
        self.step2_btn = ttk.Button(btn_frame, text="2. Расставить ударения", 
                                    command=self.run_step2, width=20, state='disabled')
        self.step2_btn.grid(row=0, column=1, padx=5)
        
        self.step3_btn = ttk.Button(btn_frame, text="3. Создать аудио", 
                                    command=self.run_step3, width=20, state='disabled')
        self.step3_btn.grid(row=0, column=2, padx=5)
        
        # Прогресс-бар
        self.progress = ttk.Progressbar(steps_frame, mode='indeterminate')
        self.progress.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        
        # Статус
        self.status_var = tk.StringVar(value="Готов к работе")
        status_label = ttk.Label(steps_frame, textvariable=self.status_var)
        status_label.grid(row=2, column=0, columnspan=2)
        
        # === Лог выполнения ===
        log_frame = ttk.LabelFrame(main_frame, text="Лог выполнения", padding="10")
        log_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, width=80)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Кнопка очистки лога
        ttk.Button(log_frame, text="Очистить лог", 
                  command=self.clear_log).grid(row=1, column=0, pady=5)
    
    def browse_work_dir(self):
        """Выбор рабочей папки"""
        dirname = filedialog.askdirectory(
            title="Выберите рабочую папку",
            initialdir=self.work_dir.get() or os.path.expanduser("~")
        )
        if dirname:
            self.work_dir.set(dirname)
            self.config.set("work_dir", dirname)
            self.init_components()
            self.log(f"Рабочая папка: {dirname}")
    
    def init_components(self):
        """Инициализация компонентов обработки"""
        work_dir = self.work_dir.get()
        if work_dir and os.path.exists(work_dir):
            Path(work_dir).mkdir(exist_ok=True)
    
    def log(self, message):
        """Добавление сообщения в лог"""
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.root.update()
    
    def clear_log(self):
        """Очистка лога"""
        self.log_text.delete(1.0, tk.END)
    
    def update_step_status(self):
        """Обновление состояния кнопок в зависимости от выполненных шагов"""
        work_dir = self.work_dir.get()
        if not work_dir or not os.path.exists(work_dir):
            return
        
        # Проверяем наличие результатов каждого этапа
        extracted_dir = Path(work_dir) / "01_extracted_text"
        accented_dir = Path(work_dir) / "02_accented_text"
        
        # Этап 1 доступен всегда
        self.step1_btn.config(state='normal')
        
        # Этап 2 доступен если есть извлечённые тексты
        if extracted_dir.exists() and list(extracted_dir.glob("*.txt")):
            self.step2_btn.config(state='normal')
        else:
            self.step2_btn.config(state='disabled')
        
        # Этап 3 доступен если есть тексты с ударениями
        if accented_dir.exists() and list(accented_dir.glob("*.txt")):
            self.step3_btn.config(state='normal')
        else:
            self.step3_btn.config(state='disabled')
    
    def run_step1(self):
        """Запуск извлечения текста"""
        if not self.work_dir.get():
            messagebox.showerror("Ошибка", "Выберите рабочую папку!")
            return
        
        def task():
            try:
                self.status_var.set("Извлечение текста...")
                self.progress.start()
                
                extractor = TextExtractor(self.work_dir.get())
                
                # Ищем все поддерживаемые файлы
                supported_ext = ['.txt', '.pdf', '.epub', '.fb2']
                processed = 0
                
                for ext in supported_ext:
                    for file_path in Path(self.work_dir.get()).glob(f"*{ext}"):
                        if file_path.is_file():
                            self.log(f"Обработка: {file_path.name}")
                            output = extractor.extract(file_path)
                            self.log(f"  → {output.name}")
                            processed += 1
                
                self.log(f"Обработано файлов: {processed}")
                self.update_step_status()
                self.status_var.set("Готов")
                
            except Exception as e:
                self.log(f"ОШИБКА: {e}")
                self.status_var.set("Ошибка")
            finally:
                self.progress.stop()
        
        threading.Thread(target=task, daemon=True).start()
    
    def run_step2(self):
        """Запуск расстановки ударений"""
        if not self.work_dir.get():
            messagebox.showerror("Ошибка", "Выберите рабочую папку!")
            return
        
        def task():
            try:
                self.status_var.set("Расстановка ударений...")
                self.progress.start()
                
                self.log("Загрузка модели ударений...")
                accentor = AccentProcessor(
                    self.work_dir.get(), 
                    model_size=self.accent_model.get()
                )
                
                results = accentor.process_all()
                
                self.log(f"Обработано файлов: {len(results)}")
                self.update_step_status()
                self.status_var.set("Готов")
                
            except Exception as e:
                self.log(f"ОШИБКА: {e}")
                self.status_var.set("Ошибка")
            finally:
                self.progress.stop()
        
        threading.Thread(target=task, daemon=True).start()
    
    def run_step3(self):
        """Запуск генерации аудио"""
        if not self.work_dir.get():
            messagebox.showerror("Ошибка", "Выберите рабочую папку!")
            return
        
        # Сохраняем текущие настройки
        self.config.set("voice", self.voice.get())
        self.config.set("speed", self.speed.get())
        self.config.set("output_format", self.output_format.get())
        
        def task():
            try:
                self.status_var.set("Генерация аудио...")
                self.progress.start()
                
                self.log("Загрузка TTS модели (Silero)...")
                self.log(f"  Голос: {self.voice.get()}")
                self.log(f"  Скорость: {self.speed.get():.1f}x")
                self.log(f"  Формат: {self.output_format.get().upper()}")
                
                audio_gen = AudioGenerator(
                    self.work_dir.get(),
                    language=self.language.get(),
                    voice=self.voice.get(),
                    speed=self.speed.get(),
                    output_format=self.output_format.get()
                )
                
                results = audio_gen.generate_all(language=self.language.get())
                
                self.log(f"Сгенерировано файлов: {len(results)}")
                self.update_step_status()
                self.status_var.set("Готов")
                
            except Exception as e:
                self.log(f"ОШИБКА: {e}")
                self.status_var.set("Ошибка")
            finally:
                self.progress.stop()
        
        threading.Thread(target=task, daemon=True).start()
    
    def on_closing(self):
        """Действия при закрытии окна"""
        # Сохраняем геометрию окна
        geometry = self.root.geometry()
        self.config.set("window_geometry", geometry)
        
        # Сохраняем последний шаг
        self.config.set("last_step", self.current_step)
        
        # Сохраняем остальные настройки
        self.config.set("accent_model", self.accent_model.get())
        self.config.set("language", self.language.get())
        self.config.set("auto_save", self.auto_save.get())
        self.config.set("voice", self.voice.get())
        self.config.set("speed", self.speed.get())
        self.config.set("output_format", self.output_format.get())
        
        self.config.save()
        self.root.destroy()