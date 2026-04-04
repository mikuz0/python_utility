# -*- coding: utf-8 -*-

"""
Виджет предпросмотра текста
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QTabWidget, QTextEdit
)
from PyQt5.QtCore import Qt

class PreviewWidget(QWidget):
    """Виджет для предпросмотра текста"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.sections = []
        self.init_ui()
    
    def init_ui(self):
        """Инициализация интерфейса"""
        layout = QVBoxLayout(self)
        
        # Заголовок
        title = QTextEdit()
        title.setPlainText("Предпросмотр")
        title.setReadOnly(True)
        title.setMaximumHeight(50)
        title.setStyleSheet("QTextEdit { background-color: #f0f0f0; font-weight: bold; }")
        layout.addWidget(title)
        
        # Вкладки для разделов
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Вкладка для исходного текста
        self.original_text_widget = QTextEdit()
        self.original_text_widget.setReadOnly(True)
        self.tab_widget.addTab(self.original_text_widget, "Исходный текст")
    
    def set_original_text(self, text):
        """Установить исходный текст"""
        self.original_text_widget.setPlainText(text)
    
    def set_sections(self, sections):
        """Установить разделы для предпросмотра"""
        self.sections = sections
        
        # Удаляем старые вкладки, кроме первой
        while self.tab_widget.count() > 1:
            self.tab_widget.removeTab(1)
        
        # Добавляем вкладки для разделов
        for section_num, content in sections:
            if content:
                text_widget = QTextEdit()
                text_widget.setPlainText(content)
                text_widget.setReadOnly(True)
                self.tab_widget.addTab(text_widget, f"Раздел {section_num}")