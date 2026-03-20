from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import sys
from pathlib import Path

from config import Config
from downloader import VideoDownloader
from utils import format_duration, format_size, VideoInfo
from conversion_settings_dialog import ConversionSettingsDialog

class DownloadWorker(QThread):
    """Рабочий поток для обработки ссылок"""
    video_info_ready = pyqtSignal(object)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, downloader, urls):
        super().__init__()
        self.downloader = downloader
        self.urls = urls
    
    def run(self):
        for url in self.urls:
            video_info = self.downloader.get_video_info(url)
            if video_info:
                self.video_info_ready.emit(video_info)
            else:
                self.error_occurred.emit(f"Не удалось получить информацию: {url}")

class VideoItemWidget(QWidget):
    """Виджет для отображения одного видео в списке"""
    
    remove_clicked = pyqtSignal(object)
    
    def __init__(self, video_info, parent=None):
        super().__init__(parent)
        self.video_info = video_info
        self.init_ui()
    
    def init_ui(self):
        layout = QHBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Чекбокс для выбора
        self.checkbox = QCheckBox()
        self.checkbox.setChecked(True)
        layout.addWidget(self.checkbox)
        
        # Информация о видео
        info_layout = QVBoxLayout()
        
        # Заголовок
        title_label = QLabel(self.video_info.title)
        title_label.setFont(QFont("Arial", 10, QFont.Bold))
        title_label.setWordWrap(True)
        info_layout.addWidget(title_label)
        
        # Детали
        details_layout = QHBoxLayout()
        
        duration_text = format_duration(self.video_info.duration)
        duration_label = QLabel(f"⏱️ {duration_text}")
        details_layout.addWidget(duration_label)
        
        # Качество
        quality_label = QLabel("📺 Качество:")
        details_layout.addWidget(quality_label)
        
        self.quality_combo = QComboBox()
        qualities = list(self.video_info.qualities.keys())
        self.quality_combo.addItems(qualities)
        if qualities:
            self.quality_combo.setCurrentIndex(0)
        details_layout.addWidget(self.quality_combo)
        
        details_layout.addStretch()
        info_layout.addLayout(details_layout)
        
        layout.addLayout(info_layout, 1)
        
        # Статус
        self.status_label = QLabel("⏳ В очереди")
        self.status_label.setMinimumWidth(150)
        layout.addWidget(self.status_label)
        
        # Прогресс
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        self.progress_bar.setFixedWidth(150)
        layout.addWidget(self.progress_bar)
        
        # Кнопка удаления
        remove_btn = QPushButton("✖")
        remove_btn.setFixedSize(25, 25)
        remove_btn.setToolTip("Удалить из списка")
        remove_btn.clicked.connect(self.on_remove_clicked)
        layout.addWidget(remove_btn)
        
        self.setLayout(layout)
    
    def on_remove_clicked(self):
        self.remove_clicked.emit(self.video_info)
    
    def update_status(self, status, progress=None):
        self.video_info.status = status
        
        if status in ["Скачивание", "Конвертация"]:
            self.status_label.setVisible(False)
            self.progress_bar.setVisible(True)
        elif status == "Завершено":
            self.status_label.setText("✅ Завершено")
            self.status_label.setVisible(True)
            self.progress_bar.setVisible(False)
        elif status == "Ошибка":
            self.status_label.setText("❌ Ошибка")
            self.status_label.setVisible(True)
            self.progress_bar.setVisible(False)
        else:
            self.status_label.setText(f"⏳ {status}")
            self.status_label.setVisible(True)
            self.progress_bar.setVisible(False)
        
        if progress is not None:
            self.progress_bar.setValue(progress)
    
    def get_selected_quality(self):
        """Возвращает выбранное качество из комбобокса"""
        if self.quality_combo.count() > 0:
            return self.quality_combo.currentText()
        return None

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.downloader = VideoDownloader()
        self.config = Config.load_config()
        self.video_items = []  # Список кортежей (widget, video_info)
        self.current_download_path = self.config.get('download_path', str(Path.home() / 'Downloads' / 'Rutube'))
        
        self.init_ui()
        self.connect_signals()
        
        # Создаем папку для загрузок, если её нет
        Path(self.current_download_path).mkdir(parents=True, exist_ok=True)
    
    def init_ui(self):
        self.setWindowTitle("Rutube Видео Загрузчик")
        self.setGeometry(100, 100, 900, 600)
        
        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Верхняя панель
        top_panel = QWidget()
        top_layout = QHBoxLayout(top_panel)
        top_layout.setContentsMargins(0, 0, 0, 0)
        
        # Поле ввода ссылок
        self.url_input = QTextEdit()
        self.url_input.setPlaceholderText("Вставьте ссылки на видео (по одной на строке)...")
        self.url_input.setMaximumHeight(80)
        top_layout.addWidget(self.url_input, 3)
        
        # Кнопки
        btn_layout = QVBoxLayout()
        
        self.add_btn = QPushButton("➕ Добавить в список")
        self.add_btn.clicked.connect(self.add_urls)
        btn_layout.addWidget(self.add_btn)
        
        self.clear_btn = QPushButton("🗑 Очистить поле")
        self.clear_btn.clicked.connect(self.clear_input)
        btn_layout.addWidget(self.clear_btn)
        
        top_layout.addLayout(btn_layout, 1)
        
        main_layout.addWidget(top_panel)
        
        # Панель с настройками
        settings_panel = QWidget()
        settings_layout = QHBoxLayout(settings_panel)
        settings_layout.setContentsMargins(0, 10, 0, 10)
        
        # Путь для сохранения
        settings_layout.addWidget(QLabel("📁 Папка:"))
        
        self.path_edit = QLineEdit()
        self.path_edit.setText(self.current_download_path)
        self.path_edit.setReadOnly(True)
        settings_layout.addWidget(self.path_edit)
        
        self.browse_btn = QPushButton("Обзор")
        self.browse_btn.clicked.connect(self.browse_folder)
        settings_layout.addWidget(self.browse_btn)
        
        settings_layout.addStretch()
        
        # Кнопка настроек конвертации
        self.conversion_settings_btn = QPushButton("⚙ Настройки конвертации")
        self.conversion_settings_btn.clicked.connect(self.show_conversion_settings)
        settings_layout.addWidget(self.conversion_settings_btn)
        
        main_layout.addWidget(settings_panel)
        
        # Список видео
        list_label = QLabel("📋 Список видео для скачивания:")
        main_layout.addWidget(list_label)
        
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setMinimumHeight(300)
        
        self.video_list_widget = QWidget()
        self.video_list_layout = QVBoxLayout(self.video_list_widget)
        self.video_list_layout.addStretch()
        scroll_area.setWidget(self.video_list_widget)
        
        main_layout.addWidget(scroll_area)
        
        # Нижняя панель
        bottom_panel = QWidget()
        bottom_layout = QHBoxLayout(bottom_panel)
        bottom_layout.setContentsMargins(0, 10, 0, 0)
        
        self.select_all_cb = QCheckBox("Выбрать все")
        self.select_all_cb.stateChanged.connect(self.toggle_select_all)
        bottom_layout.addWidget(self.select_all_cb)
        
        bottom_layout.addStretch()
        
        self.download_btn = QPushButton("🚀 Скачать выбранные")
        self.download_btn.clicked.connect(self.start_download)
        self.download_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 8px;")
        bottom_layout.addWidget(self.download_btn)
        
        self.stop_btn = QPushButton("⏹ Остановить")
        self.stop_btn.clicked.connect(self.stop_download)
        self.stop_btn.setEnabled(False)
        bottom_layout.addWidget(self.stop_btn)
        
        main_layout.addWidget(bottom_panel)
        
        # Статус бар
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Готов к работе")
    
    def connect_signals(self):
        self.downloader.progress_updated.connect(self.on_progress_updated)
        self.downloader.status_updated.connect(self.on_status_updated)
        self.downloader.conversion_progress.connect(self.on_conversion_progress)
        self.downloader.conversion_log.connect(self.on_conversion_log)
        self.downloader.ffmpeg_check.connect(self.on_ffmpeg_check)
        self.downloader.download_finished.connect(self.on_download_finished)
    
    def add_urls(self):
        """Добавляет URL из текстового поля в список"""
        text = self.url_input.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "Предупреждение", "Введите ссылки на видео")
            return
        
        urls = [url.strip() for url in text.split('\n') if url.strip()]
        
        self.status_bar.showMessage(f"Обработка {len(urls)} ссылок...")
        
        # Запускаем фоновый поток для получения информации
        self.worker = DownloadWorker(self.downloader, urls)
        self.worker.video_info_ready.connect(self.add_video_to_list)
        self.worker.error_occurred.connect(self.show_error)
        self.worker.finished.connect(lambda: self.status_bar.showMessage("Готово"))
        self.worker.start()
        
        # Очищаем поле ввода
        self.url_input.clear()
    
    def add_video_to_list(self, video_info):
        """Добавляет видео в список"""
        # Проверяем, нет ли уже такого видео
        for widget, info in self.video_items:
            if info.video_id == video_info.video_id:
                QMessageBox.information(self, "Информация", f"Видео '{video_info.title}' уже в списке")
                return
        
        # Создаем виджет
        widget = VideoItemWidget(video_info)
        widget.remove_clicked.connect(self.remove_video)
        
        # Добавляем в список
        self.video_list_layout.insertWidget(self.video_list_layout.count() - 1, widget)
        self.video_items.append((widget, video_info))
        
        self.status_bar.showMessage(f"Добавлено: {video_info.title}")
    
    def remove_video(self, video_info):
        """Удаляет видео из списка"""
        for i, (widget, info) in enumerate(self.video_items):
            if info.video_id == video_info.video_id:
                widget.deleteLater()
                self.video_items.pop(i)
                self.status_bar.showMessage(f"Удалено: {info.title}")
                break
    
    def clear_input(self):
        """Очищает поле ввода"""
        self.url_input.clear()
    
    def browse_folder(self):
        """Открывает диалог выбора папки"""
        folder = QFileDialog.getExistingDirectory(
            self, 
            "Выберите папку для сохранения",
            self.current_download_path
        )
        
        if folder:
            self.current_download_path = folder
            self.path_edit.setText(folder)
            Config.set_download_path(folder)
    
    def show_conversion_settings(self):
        """Показывает диалог настроек конвертации"""
        dialog = ConversionSettingsDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            settings = dialog.get_settings()
            
            # Сохраняем настройки
            config = Config.load_config()
            config['conversion'] = settings['conversion']
            config['compatibility'] = settings['compatibility']
            Config.save_config(config)
            
            # Проверяем реальное состояние конвертации
            conversion_enabled = settings['conversion'].get('enabled', False)
            compat_enabled = settings['compatibility'].get('enabled', False)
            
            print(f"[DEBUG] Конвертация включена: {conversion_enabled}")
            print(f"[DEBUG] Совместимость включена: {compat_enabled}")
            
            # Составляем сообщение
            msg_parts = []
            
            if conversion_enabled:
                msg_parts.append("✅ Конвертация ВКЛЮЧЕНА")
                
                if compat_enabled:
                    preset_id = settings['compatibility'].get('preset', 'old_tv')
                    preset = Config.COMPATIBILITY_PRESETS.get(preset_id, {})
                    msg_parts.append(f"🛡️ Режим совместимости: {preset.get('name', '')}")
                    msg_parts.append(f"📝 {preset.get('description', '')}")
                else:
                    msg_parts.append("⚙️ Обычный режим конвертации")
                    
                # Добавляем информацию о кодеке
                codec = settings['conversion'].get('codec', 'H264')
                codec_name = Config.AVAILABLE_CODECS.get(codec, {}).get('name', codec)
                msg_parts.append(f"🎬 Кодек: {codec_name}")
            else:
                msg_parts.append("⏹️ Конвертация ОТКЛЮЧЕНА")
                msg_parts.append("Видео будет скачано в оригинальном формате")
            
            # Показываем сообщение
            QMessageBox.information(
                self, 
                "Настройки конвертации", 
                "\n\n".join(msg_parts)
            )
    
    def toggle_select_all(self, state):
        """Выбирает/снимает выбор со всех видео"""
        for widget, _ in self.video_items:
            widget.checkbox.setChecked(state == Qt.Checked)
    
    def get_selected_videos(self):
        """Возвращает список выбранных видео с их качеством"""
        selected = []
        for widget, video_info in self.video_items:
            if widget.checkbox.isChecked():
                # Получаем выбранное качество из комбобокса
                quality = widget.get_selected_quality()
                if quality:
                    video_info.selected_quality = quality
                    print(f"[DEBUG] Выбрано качество для {video_info.title}: {quality}")
                else:
                    print(f"[WARNING] Для видео {video_info.title} не выбрано качество")
                selected.append((widget, video_info))
        return selected
    
    def start_download(self):
        """Запускает скачивание выбранных видео"""
        selected = self.get_selected_videos()
        
        if not selected:
            QMessageBox.warning(self, "Предупреждение", "Выберите видео для скачивания")
            return
        
        # Проверяем, что для каждого видео есть качества
        for widget, video_info in selected:
            if not video_info.qualities:
                QMessageBox.warning(
                    self, 
                    "Ошибка", 
                    f"Для видео '{video_info.title}' нет доступных качеств"
                )
                return
        
        # Получаем настройки конвертации
        config = Config.load_config()
        conversion_settings = config.get('conversion', {})
        
        print(f"[DEBUG] Настройки конвертации при старте: {conversion_settings}")
        
        # Очищаем очередь
        self.downloader.download_queue = []
        
        # Добавляем видео в очередь
        for widget, video_info in selected:
            self.downloader.add_to_queue(
                video_info, 
                self.current_download_path,
                quality=video_info.selected_quality,
                conversion_settings=conversion_settings
            )
            widget.update_status("В очереди")
            print(f"[DEBUG] Добавлено в очередь: {video_info.title} (качество: {video_info.selected_quality})")
        
        # Запускаем скачивание
        self.downloader.start()
        
        # Обновляем интерфейс
        self.download_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.add_btn.setEnabled(False)
        self.conversion_settings_btn.setEnabled(False)
        self.status_bar.showMessage("Скачивание начато...")
    
    def stop_download(self):
        """Останавливает скачивание"""
        self.downloader.stop()
        self.stop_btn.setEnabled(False)
        self.status_bar.showMessage("Скачивание остановлено")
    
    def on_progress_updated(self, video_id, progress, total_size):
        """Обновляет прогресс скачивания"""
        for widget, video_info in self.video_items:
            if video_info.video_id == video_id:
                widget.update_status("Скачивание", progress)
                size_text = format_size(total_size) if total_size > 0 else "Неизвестно"
                self.status_bar.showMessage(f"Скачивание: {video_info.title} ({size_text})")
                break
    
    def on_conversion_progress(self, video_id, progress):
        """Обновляет прогресс конвертации"""
        for widget, video_info in self.video_items:
            if video_info.video_id == video_id:
                widget.update_status("Конвертация", progress)
                self.status_bar.showMessage(f"Конвертация: {video_info.title} ({progress}%)")
                break
    
    def on_conversion_log(self, video_id, log_message):
        """Обрабатывает логи конвертации"""
        # Можно добавить окно с логами
        pass
    
    def on_ffmpeg_check(self, available, version):
        """Обрабатывает результат проверки FFmpeg"""
        if not available:
            reply = QMessageBox.warning(
                self, 
                "FFmpeg не найден",
                "FFmpeg не установлен или не найден в системе.\n\n"
                "Конвертация видео будет недоступна.\n\n"
                "Хотите скачать FFmpeg?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                import webbrowser
                webbrowser.open("https://ffmpeg.org/download.html")
        else:
            self.status_bar.showMessage(f"FFmpeg найден (версия {version})")
    
    def on_status_updated(self, video_id, status):
        """Обновляет статус видео"""
        for widget, video_info in self.video_items:
            if video_info.video_id == video_id:
                widget.update_status(status)
                break
    
    def on_download_finished(self, video_id, success, message):
        """Обрабатывает завершение скачивания"""
        for widget, video_info in self.video_items:
            if video_info.video_id == video_id:
                if success:
                    parts = message.split('|')
                    status_msg = parts[0]
                    output_path = parts[1] if len(parts) > 1 else None
                    
                    widget.update_status("Завершено")
                    
                    if output_path and self.config.get('auto_open_folder', False):
                        import subprocess
                        import platform
                        
                        output_dir = str(Path(output_path).parent)
                        
                        if platform.system() == 'Windows':
                            subprocess.run(['explorer', output_dir])
                        elif platform.system() == 'Darwin':
                            subprocess.run(['open', output_dir])
                        else:
                            subprocess.run(['xdg-open', output_dir])
                    
                    self.status_bar.showMessage(f"✅ Завершено: {video_info.title}")
                else:
                    widget.update_status("Ошибка")
                    self.status_bar.showMessage(f"❌ Ошибка: {video_info.title} - {message}")
                break
        
        # Проверяем, все ли видео скачаны
        all_finished = all(
            info.status in ["Завершено", "Ошибка"] 
            for _, info in self.video_items 
            if info in self.downloader.download_queue
        )
        
        if all_finished:
            self.download_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
            self.add_btn.setEnabled(True)
            self.conversion_settings_btn.setEnabled(True)
            self.status_bar.showMessage("Все задачи выполнены")
    
    def show_error(self, message):
        """Показывает ошибку"""
        QMessageBox.warning(self, "Ошибка", message)
    
    def closeEvent(self, event):
        """Обрабатывает закрытие окна"""
        if self.downloader.is_running:
            reply = QMessageBox.question(
                self, "Подтверждение",
                "Скачивание ещё выполняется. Завершить?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.downloader.stop()
                self.downloader.wait()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()