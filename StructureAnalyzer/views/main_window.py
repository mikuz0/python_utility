# -*- coding: utf-8 -*-

import os
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QTreeWidget, QTreeWidgetItem,
                             QFileDialog, QLabel, QMessageBox, QSplitter,
                             QTextEdit, QStatusBar, QGroupBox, QFormLayout)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QColor, QBrush

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.project_parser import ProjectParser, ProjectNode
from models.file_system_analyzer import FileSystemAnalyzer

class MainWindow(QMainWindow):
    """Главное окно приложения"""
    
    def __init__(self):
        super().__init__()
        self.project_parser = ProjectParser()
        self.file_analyzer = FileSystemAnalyzer()
        self.current_project_file = None
        self.project_root = None
        self.current_root_path = None
        
        self.init_ui()
        
    def init_ui(self):
        """Инициализация интерфейса"""
        self.setWindowTitle("DPCreator Analyzer")
        self.setGeometry(100, 100, 1200, 800)
        
        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Основной layout
        layout = QVBoxLayout(central_widget)
        
        # Верхняя панель с информацией
        info_panel = QGroupBox("Информация о проекте")
        info_layout = QFormLayout(info_panel)
        
        self.lbl_structure_file = QLabel("Не выбран")
        self.lbl_structure_file.setWordWrap(True)
        info_layout.addRow("Файл структуры:", self.lbl_structure_file)
        
        self.lbl_project_root = QLabel("Не определен")
        self.lbl_project_root.setWordWrap(True)
        info_layout.addRow("Корневая директория:", self.lbl_project_root)
        
        self.lbl_root_path = QLabel("Не выбран")
        self.lbl_root_path.setWordWrap(True)
        info_layout.addRow("Путь для анализа:", self.lbl_root_path)
        
        layout.addWidget(info_panel)
        
        # Панель с кнопками
        buttons_panel = QHBoxLayout()
        
        self.btn_open_structure = QPushButton("1. Открыть файл структуры")
        self.btn_open_structure.clicked.connect(self.open_structure_file)
        self.btn_open_structure.setMinimumHeight(40)
        buttons_panel.addWidget(self.btn_open_structure)
        
        self.btn_select_root = QPushButton("2. Выбрать корневую директорию")
        self.btn_select_root.clicked.connect(self.select_root_directory)
        self.btn_select_root.setEnabled(False)
        self.btn_select_root.setMinimumHeight(40)
        buttons_panel.addWidget(self.btn_select_root)
        
        self.btn_analyze = QPushButton("3. Анализировать")
        self.btn_analyze.clicked.connect(self.analyze_structure)
        self.btn_analyze.setEnabled(False)
        self.btn_analyze.setMinimumHeight(40)
        self.btn_analyze.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
            }
            QPushButton:hover {
                background-color: #2ecc71;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
        """)
        buttons_panel.addWidget(self.btn_analyze)
        
        buttons_panel.addStretch()
        
        layout.addLayout(buttons_panel)
        
        # Быстрый поиск корневой директории
        quick_panel = QHBoxLayout()
        quick_panel.addWidget(QLabel("Быстрый переход:"))
        
        self.btn_use_current = QPushButton("Текущая директория")
        self.btn_use_current.clicked.connect(self.use_current_directory)
        self.btn_use_current.setEnabled(False)
        quick_panel.addWidget(self.btn_use_current)
        
        self.btn_use_parent = QPushButton("Родительская директория")
        self.btn_use_parent.clicked.connect(self.use_parent_directory)
        self.btn_use_parent.setEnabled(False)
        quick_panel.addWidget(self.btn_use_parent)
        
        self.btn_use_suggested = QPushButton("Предложенная")
        self.btn_use_suggested.clicked.connect(self.use_suggested_directory)
        self.btn_use_suggested.setEnabled(False)
        self.btn_use_suggested.setStyleSheet("background-color: #f39c12;")
        quick_panel.addWidget(self.btn_use_suggested)
        
        quick_panel.addStretch()
        
        layout.addLayout(quick_panel)
        
        # Разделитель для древовидного представления и лога
        splitter = QSplitter(Qt.Horizontal)
        
        # Древовидное представление
        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderLabels(["Элемент", "Тип", "Статус"])
        self.tree_widget.setColumnWidth(0, 350)
        self.tree_widget.setColumnWidth(1, 80)
        self.tree_widget.setColumnWidth(2, 120)
        self.tree_widget.itemDoubleClicked.connect(self.on_item_double_clicked)
        splitter.addWidget(self.tree_widget)
        
        # Текстовое поле для лога
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumWidth(350)
        self.log_text.setFont(QFont("Consolas", 9))
        splitter.addWidget(self.log_text)
        
        # Устанавливаем пропорции разделителя
        splitter.setSizes([750, 350])
        
        layout.addWidget(splitter)
        
        # Статус бар
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Готов к работе")
        
        # Применяем стили
        self.apply_styles()
        
    def apply_styles(self):
        """Применение стилей"""
        self.tree_widget.setStyleSheet("""
            QTreeWidget {
                alternate-background-color: #f8f9fa;
            }
            QTreeWidget::item {
                padding: 4px;
                border-bottom: 1px solid #e9ecef;
            }
            QTreeWidget::item:selected {
                background-color: #3498db;
                color: white;
            }
            QTreeWidget::item:hover {
                background-color: #e9ecef;
            }
        """)
        
    def open_structure_file(self):
        """Открытие файла со структурой"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "Выберите файл структуры",
            "",
            "Текстовые файлы (*.txt);;Все файлы (*.*)"
        )
        
        if file_path:
            self.current_project_file = file_path
            self.lbl_structure_file.setText(os.path.basename(file_path))
            self.lbl_structure_file.setToolTip(file_path)
            
            # Парсим файл
            self.project_root = self.project_parser.parse_file(file_path)
            
            if self.project_root:
                root_name = self.project_parser.get_root_dir_name()
                self.lbl_project_root.setText(root_name)
                
                self.log_message(f"✅ Файл структуры загружен: {file_path}")
                self.log_message(f"📁 Корневая директория проекта: {root_name}")
                
                # Отображаем структуру
                self.display_structure(self.project_root)
                
                # Активируем кнопки
                self.btn_select_root.setEnabled(True)
                self.btn_use_current.setEnabled(True)
                self.btn_use_parent.setEnabled(True)
                
                # Проверяем, есть ли предположительная корневая директория
                suggested = self.file_analyzer.suggest_root_path(root_name)
                if suggested:
                    self.btn_use_suggested.setEnabled(True)
                    self.btn_use_suggested.setToolTip(f"Использовать: {suggested}")
                    self.log_message(f"💡 Найдена предполагаемая корневая директория: {suggested}")
                else:
                    self.btn_use_suggested.setEnabled(False)
                
                self.status_bar.showMessage(f"Загружено: {os.path.basename(file_path)}")
            else:
                QMessageBox.critical(self, "Ошибка", "Не удалось распарсить файл структуры")
                self.log_message("❌ Ошибка при парсинге файла структуры")
    
    def select_root_directory(self):
        """Выбор корневой директории для анализа"""
        directory = QFileDialog.getExistingDirectory(
            self,
            "Выберите корневую директорию проекта",
            self.current_root_path if self.current_root_path else os.path.expanduser("~")
        )
        
        if directory:
            self.set_root_directory(directory)
    
    def set_root_directory(self, directory: str):
        """Установка корневой директории"""
        self.current_root_path = directory
        self.file_analyzer.set_root_path(directory)
        self.lbl_root_path.setText(directory)
        self.btn_analyze.setEnabled(True)
        
        # Подсвечиваем кнопку анализа
        self.btn_analyze.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2ecc71;
            }
        """)
        
        self.log_message(f"📂 Выбрана корневая директория: {directory}")
        self.status_bar.showMessage(f"Корневая директория: {directory}")
    
    def use_current_directory(self):
        """Использовать текущую рабочую директорию"""
        current = os.getcwd()
        self.set_root_directory(current)
    
    def use_parent_directory(self):
        """Использовать родительскую директорию"""
        parent = os.path.dirname(os.getcwd())
        if parent and parent != os.getcwd():
            self.set_root_directory(parent)
        else:
            QMessageBox.information(self, "Информация", "Нет родительской директории")
    
    def use_suggested_directory(self):
        """Использовать предположительную корневую директорию"""
        if self.project_root:
            suggested = self.file_analyzer.suggest_root_path(
                self.project_parser.get_root_dir_name()
            )
            if suggested:
                self.set_root_directory(suggested)
    
    def analyze_structure(self):
        """Анализ структуры"""
        if not self.project_root or not self.current_root_path:
            QMessageBox.warning(
                self, 
                "Предупреждение", 
                "Сначала выберите файл структуры и корневую директорию"
            )
            return
        
        self.log_message("\n" + "="*60)
        self.log_message("🔍 НАЧАЛО АНАЛИЗА")
        self.log_message("="*60)
        self.log_message(f"Файл структуры: {self.current_project_file}")
        self.log_message(f"Корневая директория: {self.current_root_path}")
        
        # Выполняем анализ
        result = self.file_analyzer.analyze(self.project_root)
        
        # Обновляем отображение
        self.display_structure(self.project_root)
        
        # Выводим статистику
        total_files = sum(1 for node in self.get_all_nodes(self.project_root) if node.is_file)
        total_dirs = sum(1 for node in self.get_all_nodes(self.project_root) if not node.is_file)
        
        self.log_message(f"\n📊 СТАТИСТИКА:")
        self.log_message(f"   Всего элементов: {total_files + total_dirs}")
        self.log_message(f"   - Файлы: {total_files}")
        self.log_message(f"   - Директории: {total_dirs}")
        self.log_message(f"\n✅ Существующие файлы: {len(result['existing'])}")
        self.log_message(f"❌ Отсутствующие файлы: {len(result['missing'])}")
        self.log_message(f"📁 Пустые директории: {len(result['empty_dirs'])}")
        
        if result['missing']:
            self.log_message("\n❌ ОТСУТСТВУЮЩИЕ ФАЙЛЫ:")
            for i, file in enumerate(result['missing'][:20], 1):
                self.log_message(f"   {i:2d}. {os.path.basename(file)}")
            if len(result['missing']) > 20:
                self.log_message(f"   ... и еще {len(result['missing']) - 20}")
        
        if result['empty_dirs']:
            self.log_message("\n📁 ПУСТЫЕ ДИРЕКТОРИИ:")
            for i, dir_path in enumerate(result['empty_dirs'][:10], 1):
                self.log_message(f"   {i:2d}. {os.path.basename(dir_path)}")
            if len(result['empty_dirs']) > 10:
                self.log_message(f"   ... и еще {len(result['empty_dirs']) - 10}")
        
        self.log_message("\n" + "="*60)
        self.log_message("✅ АНАЛИЗ ЗАВЕРШЕН")
        
        # Обновляем статус
        self.status_bar.showMessage(
            f"Анализ завершен. Найдено: {len(result['existing'])} существующих, "
            f"{len(result['missing'])} отсутствующих, {len(result['empty_dirs'])} пустых"
        )
        
        # Показываем всплывающее уведомление
        QTimer.singleShot(100, lambda: self.show_analysis_summary(result))
    
    def show_analysis_summary(self, result):
        """Показать сводку анализа"""
        QMessageBox.information(
            self,
            "Результаты анализа",
            f"<b>Анализ завершен!</b><br><br>"
            f"✅ Существующие файлы: {len(result['existing'])}<br>"
            f"❌ Отсутствующие файлы: {len(result['missing'])}<br>"
            f"📁 Пустые директории: {len(result['empty_dirs'])}<br><br>"
            f"Подробности в логе."
        )
    
    def get_all_nodes(self, node: ProjectNode) -> list:
        """Получить все узлы дерева"""
        nodes = [node]
        for child in node.children:
            nodes.extend(self.get_all_nodes(child))
        return nodes
    
    def display_structure(self, node: ProjectNode, parent_item: QTreeWidgetItem = None):
        """Отображение структуры в дереве"""
        self.tree_widget.clear()
        
        def add_node(node: ProjectNode, parent_item: QTreeWidgetItem = None):
            if parent_item is None:
                item = QTreeWidgetItem(self.tree_widget)
            else:
                item = QTreeWidgetItem(parent_item)
            
            # Устанавливаем текст
            item.setText(0, node.name)
            item.setText(1, "Файл" if node.is_file else "Папка")
            
            # Определяем статус и цвет
            if node.is_file:
                if node.exists:
                    status = "✓ Существует"
                    color = QColor(39, 174, 96)  # Зеленый
                else:
                    status = "✗ Отсутствует"
                    color = QColor(192, 57, 43)  # Красный
            else:
                if node.is_empty:
                    status = "○ Пустая"
                    color = QColor(243, 156, 18)  # Оранжевый
                elif not node.exists:
                    status = "✗ Отсутствует"
                    color = QColor(192, 57, 43)  # Красный
                else:
                    status = "✓ Существует"
                    color = QColor(39, 174, 96)  # Зеленый
            
            item.setText(2, status)
            item.setForeground(0, QBrush(color))
            item.setForeground(2, QBrush(color))
            
            # Сохраняем полный путь к узлу
            item.setData(0, Qt.UserRole, node)
            
            # Добавляем иконку
            if node.is_file:
                if node.exists:
                    item.setIcon(0, self.style().standardIcon(self.style().SP_FileIcon))
                else:
                    item.setIcon(0, self.style().standardIcon(self.style().SP_FileLinkIcon))
            else:
                if node.exists:
                    item.setIcon(0, self.style().standardIcon(self.style().SP_DirIcon))
                else:
                    item.setIcon(0, self.style().standardIcon(self.style().SP_DirLinkIcon))
            
            # Добавляем подсказку с полным путем
            if hasattr(node, 'full_path') and node.full_path:
                item.setToolTip(0, node.full_path)
            
            # Рекурсивно добавляем детей в правильном порядке
            dirs = [child for child in node.children if not child.is_file]
            files = [child for child in node.children if child.is_file]
            
            for child in sorted(dirs, key=lambda x: x.name):
                add_node(child, item)
            
            for child in sorted(files, key=lambda x: x.name):
                add_node(child, item)
        
        add_node(node)
        self.tree_widget.expandToDepth(1)
    
    def on_item_double_clicked(self, item: QTreeWidgetItem, column: int):
        """Обработка двойного клика по элементу"""
        node = item.data(0, Qt.UserRole)
        
        if node and node.is_file and node.exists and self.current_root_path:
            # Формируем полный путь к файлу
            if node.full_path:
                relative_path = node.full_path
            else:
                relative_path = node.get_full_path()
            
            if relative_path.startswith(self.project_parser.get_root_dir_name()):
                relative_path = relative_path[len(self.project_parser.get_root_dir_name()):].lstrip('/')
            
            file_path = os.path.join(self.current_root_path, relative_path)
            
            self.log_message(f"🖱️ Двойной клик: {file_path}")
            
            if self.file_analyzer.open_file(file_path):
                self.log_message(f"📄 Открыт файл: {file_path}")
            else:
                self.log_message(f"❌ Не удалось открыть файл: {file_path}")
                QMessageBox.warning(
                    self, 
                    "Ошибка", 
                    f"Не удалось открыть файл:\n{file_path}"
                )
    
    def log_message(self, message: str):
        """Добавление сообщения в лог"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
        cursor = self.log_text.textCursor()
        cursor.movePosition(cursor.End)
        self.log_text.setTextCursor(cursor)