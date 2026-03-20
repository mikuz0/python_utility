from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from config import Config

class ConversionSettingsDialog(QDialog):
    """Диалог настроек конвертации"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.config = Config.load_config()
        self.conversion_settings = self.config.get('conversion', {})
        self.compatibility_settings = self.config.get('compatibility', {})
        self.init_ui()
        self.load_settings()
    
    def init_ui(self):
        self.setWindowTitle("Настройки конвертации")
        self.setModal(True)
        self.setMinimumWidth(650)
        self.setMinimumHeight(600)
        
        layout = QVBoxLayout()
        
        # Основные настройки
        main_group = QGroupBox("Основные настройки")
        main_layout = QGridLayout()
        
        # Включить конвертацию
        self.enable_cb = QCheckBox("Включить конвертацию")
        self.enable_cb.toggled.connect(self.on_conversion_toggled)
        main_layout.addWidget(self.enable_cb, 0, 0, 1, 2)
        
        # Выбор кодека
        main_layout.addWidget(QLabel("Кодек:"), 1, 0)
        self.codec_combo = QComboBox()
        for codec_id, codec_info in Config.AVAILABLE_CODECS.items():
            self.codec_combo.addItem(codec_info['name'], codec_id)
        self.codec_combo.currentIndexChanged.connect(self.on_codec_changed)
        main_layout.addWidget(self.codec_combo, 1, 1)
        
        # Разрешение
        main_layout.addWidget(QLabel("Разрешение:"), 2, 0)
        self.resolution_combo = QComboBox()
        for res in Config.AVAILABLE_RESOLUTIONS:
            self.resolution_combo.addItem(res['name'], res)
        main_layout.addWidget(self.resolution_combo, 2, 1)
        
        # Битрейт видео
        main_layout.addWidget(QLabel("Битрейт видео:"), 3, 0)
        self.video_bitrate_combo = QComboBox()
        self.video_bitrate_combo.addItem("Авто", "auto")
        main_layout.addWidget(self.video_bitrate_combo, 3, 1)
        
        # Битрейт аудио
        main_layout.addWidget(QLabel("Битрейт аудио:"), 4, 0)
        self.audio_bitrate_combo = QComboBox()
        self.audio_bitrate_combo.addItem("Авто", "auto")
        for bitrate in Config.AVAILABLE_BITRATES['audio']:
            self.audio_bitrate_combo.addItem(f"{bitrate} kbps", bitrate)
        main_layout.addWidget(self.audio_bitrate_combo, 4, 1)
        
        main_group.setLayout(main_layout)
        layout.addWidget(main_group)
        
        # РАЗДЕЛ СОВМЕСТИМОСТИ
        compat_group = QGroupBox("Совместимость со старыми устройствами")
        compat_group.setStyleSheet("QGroupBox { font-weight: bold; color: #2c3e50; }")
        compat_layout = QVBoxLayout()
        
        # Включить режим совместимости
        self.compat_enable_cb = QCheckBox("Включить режим совместимости")
        self.compat_enable_cb.setStyleSheet("color: #27ae60; font-weight: bold;")
        self.compat_enable_cb.toggled.connect(self.on_compat_toggled)
        compat_layout.addWidget(self.compat_enable_cb)
        
        # Информационная строка
        info_label = QLabel("⚙️ Для старых TV, DVD-плееров, первых смартфонов")
        info_label.setStyleSheet("color: #7f8c8d; font-style: italic; padding-left: 20px;")
        compat_layout.addWidget(info_label)
        
        # Пресеты совместимости
        preset_layout = QHBoxLayout()
        preset_layout.addWidget(QLabel("Пресет:"))
        self.compat_preset_combo = QComboBox()
        for preset_id, preset_info in Config.COMPATIBILITY_PRESETS.items():
            self.compat_preset_combo.addItem(preset_info['name'], preset_id)
        self.compat_preset_combo.currentIndexChanged.connect(self.on_preset_changed)
        preset_layout.addWidget(self.compat_preset_combo)
        preset_layout.addStretch()
        compat_layout.addLayout(preset_layout)
        
        # Описание пресета
        self.preset_description = QLabel("")
        self.preset_description.setStyleSheet("color: #34495e; padding: 5px; background-color: #f8f9fa; border-radius: 3px;")
        self.preset_description.setWordWrap(True)
        compat_layout.addWidget(self.preset_description)
        
        compat_group.setLayout(compat_layout)
        layout.addWidget(compat_group)
        
        # Расширенные настройки видео
        advanced_group = QGroupBox("Расширенные настройки видео")
        advanced_layout = QGridLayout()
        
        # Пресет скорости
        advanced_layout.addWidget(QLabel("Пресет скорости:"), 0, 0)
        self.preset_combo = QComboBox()
        advanced_layout.addWidget(self.preset_combo, 0, 1)
        
        # Пиксельный формат
        advanced_layout.addWidget(QLabel("Пиксельный формат:"), 1, 0)
        self.pixel_format_combo = QComboBox()
        advanced_layout.addWidget(self.pixel_format_combo, 1, 1)
        
        # Профиль H.264
        advanced_layout.addWidget(QLabel("Профиль H.264:"), 2, 0)
        self.profile_combo = QComboBox()
        advanced_layout.addWidget(self.profile_combo, 2, 1)
        
        advanced_group.setLayout(advanced_layout)
        layout.addWidget(advanced_group)
        
        # Настройки аудио
        self.audio_group = QGroupBox("Настройки аудио")
        audio_layout = QGridLayout()
        
        audio_layout.addWidget(QLabel("Частота дискретизации:"), 0, 0)
        self.sample_rate_combo = QComboBox()
        audio_layout.addWidget(self.sample_rate_combo, 0, 1)
        
        self.audio_group.setLayout(audio_layout)
        layout.addWidget(self.audio_group)
        
        # Кнопки
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        self.setLayout(layout)
    
    def load_settings(self):
        """Загружает сохраненные настройки"""
        # Основные настройки
        self.enable_cb.setChecked(self.conversion_settings.get('enabled', False))
        
        # Кодек
        codec = self.conversion_settings.get('codec', 'H264')
        index = self.codec_combo.findData(codec)
        if index >= 0:
            self.codec_combo.setCurrentIndex(index)
        
        # Разрешение
        resolution = self.conversion_settings.get('resolution', 'Original')
        index = self.resolution_combo.findText(resolution)
        if index >= 0:
            self.resolution_combo.setCurrentIndex(index)
        
        # Битрейт видео
        video_bitrate = self.conversion_settings.get('video_bitrate', 'auto')
        index = self.video_bitrate_combo.findData(video_bitrate)
        if index >= 0:
            self.video_bitrate_combo.setCurrentIndex(index)
        
        # Битрейт аудио
        audio_bitrate = self.conversion_settings.get('audio_bitrate', 192)
        index = self.audio_bitrate_combo.findData(audio_bitrate)
        if index >= 0:
            self.audio_bitrate_combo.setCurrentIndex(index)
        
        # Пресет
        preset = self.conversion_settings.get('preset', 'medium')
        self.preset_combo.setCurrentText(preset)
        
        # Пиксельный формат
        pixel_format = self.conversion_settings.get('pixel_format', 'yuv420p')
        index = self.pixel_format_combo.findData(pixel_format)
        if index >= 0:
            self.pixel_format_combo.setCurrentIndex(index)
        
        # Профиль H.264
        profile = self.conversion_settings.get('profile', 'high')
        index = self.profile_combo.findData(profile)
        if index >= 0:
            self.profile_combo.setCurrentIndex(index)
        
        # Частота дискретизации
        if 'sample_rate' in self.conversion_settings:
            sample_rate = self.conversion_settings['sample_rate']
            index = self.sample_rate_combo.findData(sample_rate)
            if index >= 0:
                self.sample_rate_combo.setCurrentIndex(index)
        
        # Настройки совместимости
        self.compat_enable_cb.setChecked(self.compatibility_settings.get('enabled', False))
        
        preset_id = self.compatibility_settings.get('preset', 'old_tv')
        index = self.compat_preset_combo.findData(preset_id)
        if index >= 0:
            self.compat_preset_combo.setCurrentIndex(index)
        
        self.update_preset_description(preset_id)
        self.on_codec_changed()
        self.on_compat_toggled(self.compat_enable_cb.isChecked())
    
    def update_preset_description(self, preset_id):
        """Обновляет описание выбранного пресета"""
        preset = Config.COMPATIBILITY_PRESETS.get(preset_id, {})
        desc = preset.get('description', '')
        self.preset_description.setText(f"ℹ️ {desc}")
    
    def on_preset_changed(self, index):
        """Обрабатывает смену пресета"""
        preset_id = self.compat_preset_combo.currentData()
        self.update_preset_description(preset_id)
    
    def on_conversion_toggled(self, enabled):
        """Обрабатывает включение/выключение конвертации"""
        self.codec_combo.setEnabled(enabled)
        self.resolution_combo.setEnabled(enabled)
        self.video_bitrate_combo.setEnabled(enabled)
        self.audio_bitrate_combo.setEnabled(enabled)
        self.preset_combo.setEnabled(enabled)
        self.pixel_format_combo.setEnabled(enabled)
        self.profile_combo.setEnabled(enabled)
        self.compat_enable_cb.setEnabled(enabled)
        self.audio_group.setEnabled(enabled)
        
        if enabled:
            self.on_codec_changed()
    
    def on_compat_toggled(self, enabled):
        """Обрабатывает включение/выключение режима совместимости"""
        self.compat_preset_combo.setEnabled(enabled)
        
        # При включении режима совместимости форсируем H.264
        if enabled:
            index = self.codec_combo.findData('H264')
            if index >= 0:
                self.codec_combo.setCurrentIndex(index)
            self.codec_combo.setEnabled(False)
            
            # Показываем информацию о принудительном H.264
            self.preset_description.setText(
                self.preset_description.text() + "\n\n"
                "⚠️ Режим совместимости использует H.264 для максимальной совместимости"
            )
        else:
            self.codec_combo.setEnabled(self.enable_cb.isChecked())
    
    def on_codec_changed(self):
        """Обновляет настройки при смене кодека"""
        codec_id = self.codec_combo.currentData()
        codec_info = Config.AVAILABLE_CODECS.get(codec_id, {})
        
        is_audio = codec_info.get('is_audio_only', False)
        is_h264 = codec_id == 'H264'
        
        self.resolution_combo.setEnabled(not is_audio and self.enable_cb.isChecked())
        self.video_bitrate_combo.setEnabled(not is_audio and self.enable_cb.isChecked())
        self.preset_combo.setEnabled(not is_audio and self.enable_cb.isChecked())
        self.pixel_format_combo.setEnabled(not is_audio and self.enable_cb.isChecked())
        self.profile_combo.setEnabled(is_h264 and self.enable_cb.isChecked())
        
        self.audio_group.setVisible(is_audio)
        
        # Обновляем списки
        self.preset_combo.clear()
        if 'presets' in codec_info:
            self.preset_combo.addItems(codec_info['presets'])
        else:
            self.preset_combo.addItems(['medium'])
        
        self.pixel_format_combo.clear()
        if 'pixel_formats' in codec_info:
            for pf in codec_info['pixel_formats']:
                self.pixel_format_combo.addItem(pf, pf)
        else:
            self.pixel_format_combo.addItem('yuv420p', 'yuv420p')
        
        self.profile_combo.clear()
        if is_h264 and 'profiles' in codec_info:
            for profile in codec_info['profiles']:
                self.profile_combo.addItem(profile, profile)
        
        self.sample_rate_combo.clear()
        if 'sample_rates' in codec_info:
            for sr in codec_info['sample_rates']:
                self.sample_rate_combo.addItem(f"{sr} Hz", sr)
    
    def get_settings(self):
        """Возвращает текущие настройки"""
        # Основные настройки конвертации
        settings = {
            'enabled': self.enable_cb.isChecked(),
            'codec': self.codec_combo.currentData(),
            'resolution': self.resolution_combo.currentText(),
            'video_bitrate': self.video_bitrate_combo.currentData(),
            'audio_bitrate': self.audio_bitrate_combo.currentData(),
            'preset': self.preset_combo.currentText(),
            'pixel_format': self.pixel_format_combo.currentData()
        }
        
        # Профиль для H.264
        if self.profile_combo.count() > 0:
            settings['profile'] = self.profile_combo.currentData()
        
        # Частота дискретизации для аудио
        if self.sample_rate_combo.count() > 0:
            settings['sample_rate'] = self.sample_rate_combo.currentData()
        
        # Настройки совместимости
        compat_settings = {
            'enabled': self.compat_enable_cb.isChecked(),
            'preset': self.compat_preset_combo.currentData()
        }
        
        # Загружаем параметры выбранного пресета
        if compat_settings['enabled']:
            preset_id = compat_settings['preset']
            preset = Config.COMPATIBILITY_PRESETS.get(preset_id, {})
            compat_settings.update(preset)
            print(f"[DEBUG] Загружен пресет совместимости: {preset_id}")
        
        print(f"[DEBUG] Conversion enabled: {settings['enabled']}")
        print(f"[DEBUG] Compatibility enabled: {compat_settings['enabled']}")
        
        return {
            'conversion': settings,
            'compatibility': compat_settings
        }