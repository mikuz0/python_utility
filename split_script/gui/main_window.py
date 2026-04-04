# -*- coding: utf-8 -*-

"""
Главное окно приложения
"""

import os
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QFileDialog, QMessageBox, QApplication
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal

from core.file_splitter import FileSplitter
from gui.widgets.preview_widget import PreviewWidget
from gui.widgets.settings_panel import SettingsPanel
from gui.widgets.log_widget import LogWidget
from gui.dialogs.about_dialog import AboutDialog

class SplitWorker(QThread):
    """Рабочий поток для разбиения файла"""
    
    progress = pyqtSignal(int, int, str)  # current, total, filepath
    finished = pyqtSignal(list)  # created_files
    error = pyqtSignal(str)  # error_message
    
    def __init__(self, filepath, output_dir, settings):
        super().__init__()
        self.filepath = filepath
        self.output_dir = output_dir
        self.settings = settings
    
    def run(self):
        """Запуск обработки"""
        try:
            splitter = FileSplitter()
            
            # Настраиваем процессор, передавая словарь настроек
            splitter.set_processor_config(settings=self.settings)
            
            # Загружаем файл
            text = splitter.load_file(self.filepath)
            
            # Разбиваем текст
            sections = splitter.split_text(text)
            
            if not sections:
                self.error.emit("В тексте не найдено маркеров")
                return
            
            # Сохраняем разделы
            created_files = splitter.save_sections(
                sections,
                self.filepath,
                self.output_dir,
                self.progress.emit
            )
            
            self.finished.emit(created_files)
            
        except Exception as e:
            self.error.emit(str(e))


class MainWindow(QMainWindow):
    """Главное окно приложения"""
    
    def __init__(self):
        super().__init__()
        self.current_file = None
        self.output_dir = None
        self.worker = None
        
        self.init_ui()
        
    def init_ui(self):
        """Инициализация интерфейса"""
        self.setWindowTitle("Text Splitter - Разбиение текста на файлы")
        self.setGeometry(100, 100, 1200, 800)
        
        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Главный layout
        main_layout = QVBoxLayout(central_widget)
        
        # Верхняя панель (управление файлами)
        top_panel = self.create_top_panel()
        main_layout.addLayout(top_panel)
        
        # Основной сплиттер (горизонтальный)
        splitter = QSplitter(Qt.Horizontal)
        
        # Левая панель - предпросмотр
        self.preview_widget = PreviewWidget()
        splitter.addWidget(self.preview_widget)
        
        # Правая панель - настройки и лог
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        self.settings_panel = SettingsPanel()
        self.settings_panel.settings_changed.connect(self.on_settings_changed)
        right_layout.addWidget(self.settings_panel)
        
        self.log_widget = LogWidget()
        right_layout.addWidget(self.log_widget)
        
        splitter.addWidget(right_widget)
        
        # Устанавливаем пропорции
        splitter.setSizes([600, 400])
        
        main_layout.addWidget(splitter)
        
        # Нижняя панель (кнопки действий)
        bottom_panel = self.create_bottom_panel()
        main_layout.addLayout(bottom_panel)
        
        # Статус бар
        self.statusBar().showMessage("Готов")
    
    def create_top_panel(self):
        """Создание верхней панели"""
        layout = QHBoxLayout()
        
        # Кнопка открыть файл
        self.open_btn = self.create_button("Открыть файл", self.open_file)
        layout.addWidget(self.open_btn)
        
        # Путь к файлу
        self.file_path_label = self.create_label("Файл не выбран")
        layout.addWidget(self.file_path_label)
        
        layout.addStretch()
        
        # Кнопка выбрать папку
        self.output_btn = self.create_button("Папка сохранения", self.select_output_dir)
        layout.addWidget(self.output_btn)
        
        # Путь к папке
        self.output_path_label = self.create_label("Не выбрана")
        layout.addWidget(self.output_path_label)
        
        return layout
    
    def create_bottom_panel(self):
        """Создание нижней панели"""
        layout = QHBoxLayout()
        
        layout.addStretch()
        
        # Кнопка запуска
        self.run_btn = self.create_button("Разбить на файлы", self.run_split)
        self.run_btn.setEnabled(False)
        layout.addWidget(self.run_btn)
        
        # Кнопка о программе
        about_btn = self.create_button("О программе", self.show_about)
        layout.addWidget(about_btn)
        
        return layout
    
    def create_button(self, text, callback):
        """Создание кнопки"""
        from PyQt5.QtWidgets import QPushButton
        btn = QPushButton(text)
        btn.clicked.connect(callback)
        return btn
    
    def create_label(self, text):
        """Создание метки"""
        from PyQt5.QtWidgets import QLabel
        label = QLabel(text)
        label.setStyleSheet("QLabel { color: #666; }")
        return label
    
    def open_file(self):
        """Открыть файл"""
        filepath, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите текстовый файл",
            "",
            "Текстовые файлы (*.txt);;Все файлы (*.*)"
        )
        
        if filepath:
            self.current_file = filepath
            self.file_path_label.setText(os.path.basename(filepath))
            self.statusBar().showMessage(f"Загружен файл: {filepath}")
            
            # Загружаем и отображаем текст
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    text = f.read()
                self.preview_widget.set_original_text(text)
                self.check_run_enabled()
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить файл: {e}")
    
    def select_output_dir(self):
        """Выбрать папку для сохранения"""
        output_dir = QFileDialog.getExistingDirectory(
            self,
            "Выберите папку для сохранения"
        )
        
        if output_dir:
            self.output_dir = output_dir
            self.output_path_label.setText(output_dir)
            # Обновляем настройки
            settings = self.settings_panel.get_settings()
            settings['output_dir'] = output_dir
            self.settings_panel.set_settings(settings)
            self.check_run_enabled()
    
    def check_run_enabled(self):
        """Проверить, можно ли запустить обработку"""
        enabled = self.current_file is not None and self.output_dir is not None
        self.run_btn.setEnabled(enabled)
    
    def on_settings_changed(self):
        """Обработчик изменения настроек"""
        if self.current_file:
            # Обновляем предпросмотр
            try:
                splitter = FileSplitter()
                
                # Получаем настройки
                settings = self.settings_panel.get_settings()
                
                # Если в настройках есть output_dir, обновляем его в интерфейсе
                if 'output_dir' in settings and settings['output_dir']:
                    self.output_dir = settings['output_dir']
                    self.output_path_label.setText(settings['output_dir'])
                    self.check_run_enabled()
                
                # Применяем настройки
                splitter.set_processor_config(settings=settings)
                
                # Загружаем текст
                text = splitter.load_file(self.current_file)
                
                # Разбиваем и показываем предпросмотр
                sections = splitter.split_text(text)
                self.preview_widget.set_sections(sections)
                
            except Exception as e:
                self.log_widget.add_message(f"Ошибка предпросмотра: {e}")
    
    def run_split(self):
        """Запуск разбиения"""
        if not self.current_file or not self.output_dir:
            return
        
        # Получаем настройки
        settings = self.settings_panel.get_settings()
        
        # Очищаем лог
        self.log_widget.clear()
        
        # Блокируем кнопку
        self.run_btn.setEnabled(False)
        self.statusBar().showMessage("Обработка...")
        
        # Создаем и запускаем рабочий поток
        self.worker = SplitWorker(self.current_file, self.output_dir, settings)
        self.worker.progress.connect(self.on_progress)
        self.worker.finished.connect(self.on_finished)
        self.worker.error.connect(self.on_error)
        self.worker.start()
    
    def on_progress(self, current, total, filepath):
        """Обработчик прогресса"""
        self.log_widget.add_message(f"Создан файл: {os.path.basename(filepath)}")
        self.statusBar().showMessage(f"Обработано {current} из {total}...")
    
    def on_finished(self, created_files):
        """Обработчик завершения"""
        self.run_btn.setEnabled(True)
        self.statusBar().showMessage(f"Готово! Создано файлов: {len(created_files)}")
        self.log_widget.add_message(f"Обработка завершена. Создано {len(created_files)} файлов.")
        
        QMessageBox.information(
            self,
            "Завершено",
            f"Разбиение завершено!\nСоздано файлов: {len(created_files)}\n"
            f"Папка: {self.output_dir}"
        )
    
    def on_error(self, error_message):
        """Обработчик ошибки"""
        self.run_btn.setEnabled(True)
        self.statusBar().showMessage("Ошибка")
        self.log_widget.add_message(f"ОШИБКА: {error_message}")
        QMessageBox.critical(self, "Ошибка", error_message)
    
    def show_about(self):
        """Показать окно 'О программе'"""
        about_dialog = AboutDialog(self)
        about_dialog.exec_()