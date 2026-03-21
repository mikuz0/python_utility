# -*- coding: utf-8 -*-

import os
import platform
import subprocess
from typing import Dict, List, Set
from .project_parser import ProjectNode, ProjectParser

class FileSystemAnalyzer:
    """Анализатор файловой системы для сравнения с проектной структурой"""
    
    def __init__(self):
        self.root_path = None
        self.missing_files = []
        self.empty_dirs = []
        
    def set_root_path(self, root_path: str):
        """Установка корневого пути для анализа"""
        self.root_path = root_path
        print(f"Установлен корневой путь: {root_path}")
        
    def analyze(self, project_node: ProjectNode) -> Dict:
        """Анализ существующей файловой системы"""
        if not self.root_path:
            print("Ошибка: не установлен корневой путь")
            return {
                'existing': [],
                'missing': [],
                'empty_dirs': []
            }
        
        print(f"\nНачинаем анализ. Корневой путь: {self.root_path}")
        print(f"Корневой узел: {project_node.name}")
        
        result = {
            'existing': [],
            'missing': [],
            'empty_dirs': []
        }
        
        # Очищаем предыдущие результаты
        self.missing_files = []
        self.empty_dirs = []
        
        def check_node(node: ProjectNode, base_path: str, relative_path: str = ""):
            """Рекурсивная проверка узла"""
            
            # Формируем полный путь
            if relative_path:
                full_path = os.path.join(base_path, relative_path, node.name)
                check_relative = os.path.join(relative_path, node.name)
            else:
                full_path = os.path.join(base_path, node.name)
                check_relative = node.name
            
            print(f"\nПроверка: {check_relative}")
            print(f"  Полный путь: {full_path}")
            print(f"  Тип: {'файл' if node.is_file else 'папка'}")
            
            if node.is_file:
                # Специальная обработка для __init__.py
                if node.name == "__init__.py":
                    # Проверяем оба варианта: __init__.py и init.py
                    dir_path = os.path.dirname(full_path)
                    alt_path = os.path.join(dir_path, "init.py")
                    if os.path.exists(alt_path) and os.path.isfile(alt_path):
                        node.exists = True
                        node.name = "init.py"  # Обновляем имя на реальное
                        result['existing'].append(alt_path)
                        print(f"  ✅ Найден как init.py")
                        return
                
                # Обычная проверка файла
                node.exists = os.path.exists(full_path) and os.path.isfile(full_path)
                if node.exists:
                    print(f"  ✅ Файл существует")
                    result['existing'].append(full_path)
                else:
                    print(f"  ❌ Файл отсутствует")
                    result['missing'].append(full_path)
                    self.missing_files.append(full_path)
            else:
                # Это директория
                if os.path.exists(full_path) and os.path.isdir(full_path):
                    node.exists = True
                    print(f"  ✅ Папка существует")
                    result['existing'].append(full_path)
                    
                    # Проверяем содержимое директории
                    try:
                        actual_files = os.listdir(full_path)
                        print(f"  Содержимое папки: {actual_files}")
                        
                        # Проверяем, пустая ли директория
                        if not actual_files:
                            node.is_empty = True
                            result['empty_dirs'].append(full_path)
                            self.empty_dirs.append(full_path)
                            print(f"  📁 Папка пустая")
                    except (OSError, PermissionError) as e:
                        print(f"  ⚠ Ошибка чтения папки: {e}")
                    
                    # Рекурсивно проверяем детей
                    for child in node.children:
                        check_node(child, base_path, check_relative)
                else:
                    node.exists = False
                    print(f"  ❌ Папка отсутствует")
                    result['missing'].append(full_path)
                    
                    # Помечаем всех детей как отсутствующих
                    def mark_missing(subnode):
                        subnode.exists = False
                        for child in subnode.children:
                            mark_missing(child)
                    
                    mark_missing(node)
        
        # Начинаем анализ с корневого узла
        # Проверяем, существует ли корневая папка
        root_full_path = os.path.join(self.root_path, project_node.name)
        if os.path.exists(root_full_path) and os.path.isdir(root_full_path):
            print(f"\nКорневая папка найдена: {root_full_path}")
            # Анализируем содержимое корневой папки
            for child in project_node.children:
                check_node(child, root_full_path)
        else:
            print(f"\nКорневая папка не найдена: {root_full_path}")
            # Ищем файлы непосредственно в корневой директории
            print(f"Ищем файлы непосредственно в: {self.root_path}")
            for child in project_node.children:
                check_node(child, self.root_path)
        
        print(f"\nАнализ завершен. Найдено:")
        print(f"  Существующих: {len(result['existing'])}")
        print(f"  Отсутствующих: {len(result['missing'])}")
        print(f"  Пустых папок: {len(result['empty_dirs'])}")
        
        return result
    
    def get_directory_contents(self, path: str) -> List[str]:
        """Получить содержимое директории"""
        try:
            return os.listdir(path)
        except (OSError, FileNotFoundError, PermissionError):
            return []
    
    def open_file(self, file_path: str) -> bool:
        """Открыть файл в системном редакторе"""
        try:
            if os.path.exists(file_path) and os.path.isfile(file_path):
                print(f"Открываем файл: {file_path}")
                if platform.system() == 'Windows':
                    os.startfile(file_path)
                elif platform.system() == 'Darwin':  # macOS
                    subprocess.run(['open', file_path])
                else:  # Linux
                    subprocess.run(['xdg-open', file_path])
                return True
        except Exception as e:
            print(f"Ошибка при открытии файла {file_path}: {e}")
        return False
    
    def suggest_root_path(self, project_root_name: str) -> str:
        """Предложить путь к корневой директории на основе имени из файла"""
        if not project_root_name:
            return ""
        
        # Ищем в текущей директории
        current_dir = os.getcwd()
        possible_path = os.path.join(current_dir, project_root_name)
        if os.path.exists(possible_path) and os.path.isdir(possible_path):
            return possible_path
        
        # Ищем на уровень выше
        parent_dir = os.path.dirname(current_dir)
        possible_path = os.path.join(parent_dir, project_root_name)
        if os.path.exists(possible_path) and os.path.isdir(possible_path):
            return possible_path
        
        # Ищем в текущей директории без добавления имени
        if os.path.exists(current_dir):
            return current_dir
        
        return ""