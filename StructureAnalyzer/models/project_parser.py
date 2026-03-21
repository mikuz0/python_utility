# -*- coding: utf-8 -*-

import os
import re
from typing import Dict, List, Tuple, Optional

class ProjectNode:
    """Узел структуры проекта"""
    def __init__(self, name: str, path: str = "", is_file: bool = False):
        self.name = name
        self.path = path
        self.is_file = is_file
        self.children = []
        self.parent = None
        self.exists = False
        self.is_empty = False
        self.level = 0
        self.full_path = ""
        
    def add_child(self, child):
        child.parent = self
        child.level = self.level + 1
        if self.full_path:
            child.full_path = os.path.join(self.full_path, child.name)
        else:
            child.full_path = child.name
        self.children.append(child)
        
    def get_full_path(self) -> str:
        """Получить полный путь от корня"""
        if self.parent:
            return os.path.join(self.parent.get_full_path(), self.name)
        return self.name

class ProjectParser:
    """Парсер файла структуры проекта"""
    
    def __init__(self):
        self.root = None
        self.root_dir_name = None
        
    def parse_file(self, file_path: str) -> Optional[ProjectNode]:
        """Парсинг файла со структурой проекта"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Удаляем пустые строки и строки с только комментариями
            lines = [line.rstrip() for line in lines if line.strip() and not line.strip().startswith('#')]
            
            # Находим корневую директорию (первая строка)
            root_line = lines[0].strip()
            if root_line.endswith('/'):
                root_name = root_line.rstrip('/')
            else:
                root_name = root_line
            
            self.root = ProjectNode(root_name, "", False)
            self.root_dir_name = root_name
            self.root.full_path = root_name
            
            print(f"Корень: {root_name}")
            
            # Стек для отслеживания родителей
            # Каждый элемент стека: (узел, уровень)
            stack = [(self.root, 0)]
            
            # Обрабатываем остальные строки
            for i, line in enumerate(lines[1:], 2):
                # Определяем уровень по символам в начале строки
                level = self._determine_level(line)
                
                # Извлекаем имя
                name = self._extract_name(line)
                
                if not name:
                    continue
                
                # Очищаем имя от комментариев
                clean_name = self._clean_name(name)
                
                # Определяем тип (файл или папка)
                is_file = self._is_file(clean_name)
                
                print(f"Строка {i}: уровень={level}, имя='{clean_name}', файл={is_file}")
                
                # Создаем узел
                node = ProjectNode(clean_name, "", is_file)
                
                # Находим родителя - последний элемент в стеке с уровнем меньше текущего
                while stack and stack[-1][1] >= level:
                    stack.pop()
                
                if stack:
                    parent = stack[-1][0]
                    parent.add_child(node)
                else:
                    # Если стек пуст, добавляем к корню
                    self.root.add_child(node)
                
                # Если это папка, добавляем в стек
                if not is_file:
                    stack.append((node, level))
            
            # Выводим структуру для отладки
            if self.root:
                print("\nПостроенная структура:")
                self._print_debug(self.root)
            
            return self.root
            
        except Exception as e:
            print(f"Ошибка при парсинге файла: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _determine_level(self, line: str) -> int:
        """Определение уровня вложенности по символам в начале строки"""
        # Удаляем цветовые коды
        line = re.sub(r'\x1b\[[0-9;]*m', '', line)
        
        # Считаем уровень по количеству символов структуры
        level = 0
        i = 0
        while i < len(line):
            char = line[i]
            if char in ['├', '└']:
                level += 1
                i += 1
            elif char == '│':
                # Вертикальная черта - пропускаем, уровень не увеличиваем
                i += 1
            elif char == ' ':
                # Пробелы - считаем группы по 2 пробела
                space_count = 0
                while i < len(line) and line[i] == ' ':
                    space_count += 1
                    i += 1
                level += space_count // 2
            elif char == '─':
                i += 1
            else:
                break
        
        return level
    
    def _extract_name(self, line: str) -> str:
        """Извлечение имени из строки"""
        # Удаляем цветовые коды
        line = re.sub(r'\x1b\[[0-9;]*m', '', line)
        
        # Находим начало имени (после всех символов структуры)
        for i, char in enumerate(line):
            if char not in ['│', '├', '└', '─', ' ']:
                return line[i:].strip()
        
        return ""
    
    def _clean_name(self, name: str) -> str:
        """Очистка имени от лишних символов"""
        # Удаляем комментарии
        if '#' in name:
            name = name[:name.index('#')]
        
        # Удаляем слеши в конце
        name = name.rstrip('/')
        
        # Удаляем пробелы
        name = name.strip()
        
        return name
    
    def _is_file(self, name: str) -> bool:
        """Определение, является ли элемент файлом"""
        # Если есть расширение (точка не в начале) - это файл
        if '.' in name and not name.startswith('.'):
            parts = name.split('.')
            if len(parts) >= 2 and parts[-1]:  # есть расширение
                return True
        
        # Если заканчивается на слеш - это директория
        if name.endswith('/'):
            return False
        
        # По умолчанию считаем папкой
        return False
    
    def _print_debug(self, node: ProjectNode, level: int = 0):
        """Отладочный вывод структуры"""
        indent = "  " * level
        prefix = "📄 " if node.is_file else "📁 "
        path_info = f" [{node.full_path}]" if node.full_path else ""
        print(f"{indent}{prefix}{node.name}{path_info}")
        
        # Сортируем детей: сначала папки, потом файлы
        dirs = [child for child in node.children if not child.is_file]
        files = [child for child in node.children if child.is_file]
        
        for child in sorted(dirs, key=lambda x: x.name):
            self._print_debug(child, level + 1)
        
        for child in sorted(files, key=lambda x: x.name):
            self._print_debug(child, level + 1)
    
    def print_structure(self, node=None, level=0):
        """Вывод структуры для пользователя"""
        if node is None:
            node = self.root
            
        indent = "  " * level
        prefix = "📄 " if node.is_file else "📁 "
        status = ""
        if hasattr(node, 'exists'):
            if node.exists:
                status = " ✓"
            elif node.is_file:
                status = " ✗"
        empty = " [пусто]" if hasattr(node, 'is_empty') and node.is_empty else ""
        print(f"{indent}{prefix}{node.name}{status}{empty}")
        
        # Сортируем детей: сначала папки, потом файлы
        dirs = [child for child in node.children if not child.is_file]
        files = [child for child in node.children if child.is_file]
        
        for child in sorted(dirs, key=lambda x: x.name):
            self.print_structure(child, level + 1)
        
        for child in sorted(files, key=lambda x: x.name):
            self.print_structure(child, level + 1)
    
    def get_root_dir_name(self) -> str:
        """Получить имя корневой директории из файла структуры"""
        return self.root_dir_name if self.root_dir_name else ""