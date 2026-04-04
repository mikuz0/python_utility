# -*- coding: utf-8 -*-

"""
Модуль для обработки текста
"""

import re
import json

class TextProcessor:
    """Класс для обработки текста"""
    
    def __init__(self):
        """Инициализация процессора текста"""
        self.marker_pattern = r'^\s*(\d+)\.\s*'
        self.marker_description = "Цифры с точкой (1., 2., ...)"
        self.remove_brackets = True
        self.bracket_pairs = ['()']  # Список пар скобок для удаления
        self.remove_spaces = True
        self.normalize_punctuation = True
        self.chars_to_remove = []  # Список символов для удаления
        
    def set_marker_pattern(self, pattern, description=""):
        """Установить шаблон маркера"""
        self.marker_pattern = pattern
        self.marker_description = description
    
    def get_marker_pattern(self):
        """Получить шаблон маркера"""
        return self.marker_pattern
    
    def get_marker_description(self):
        """Получить описание маркера"""
        return self.marker_description
    
    def set_remove_brackets(self, remove):
        """Установить флаг удаления скобок"""
        self.remove_brackets = remove
    
    def set_bracket_pairs(self, pairs):
        """Установить список пар скобок"""
        self.bracket_pairs = pairs
    
    def set_remove_spaces(self, remove):
        """Установить флаг удаления лишних пробелов"""
        self.remove_spaces = remove
    
    def set_normalize_punctuation(self, normalize):
        """Установить флаг нормализации знаков препинания"""
        self.normalize_punctuation = normalize
    
    def set_chars_to_remove(self, chars):
        """Установить список символов для удаления"""
        self.chars_to_remove = chars
    
    def remove_parentheses_content(self, text):
        """
        Удаляет содержимое в указанных скобках
        
        Args:
            text: исходный текст
            
        Returns:
            текст с удаленным содержимым в скобках
        """
        result = text
        
        for pair in self.bracket_pairs:
            if len(pair) == 2:
                open_bracket = pair[0]
                close_bracket = pair[1]
                # Экранируем специальные символы regex
                open_bracket_escaped = re.escape(open_bracket)
                close_bracket_escaped = re.escape(close_bracket)
                pattern = re.compile(
                    f'{open_bracket_escaped}[^{open_bracket_escaped}{close_bracket_escaped}]*{close_bracket_escaped}',
                    re.DOTALL
                )
                result = pattern.sub('', result)
        
        return result
    
    def remove_specific_chars(self, text):
        """
        Удаляет указанные символы из текста
        
        Args:
            text: исходный текст
            
        Returns:
            текст с удаленными символами
        """
        if not self.chars_to_remove:
            return text
        
        for char in self.chars_to_remove:
            if char:
                text = text.replace(char, '')
        
        return text
    
    def remove_number_markers(self, text):
        """
        Удаляет маркеры из начала и конца текста
        
        Args:
            text: текст раздела
            
        Returns:
            текст с удаленными маркерами
        """
        # Удаляем маркер в начале текста
        pattern_start = re.compile(self.marker_pattern)
        text = pattern_start.sub('', text)
        
        # Удаляем цифру с точкой в конце текста, но оставляем саму точку
        pattern_end = re.compile(r'\s*\d+\.\s*$')
        text = pattern_end.sub('.', text)
        
        # Если после замены получилось две точки подряд, заменяем на одну
        text = re.sub(r'\.\.', '.', text)
        
        return text
    
    def clean_text(self, text):
        """
        Очищает текст: удаляет лишние пробелы и нормализует знаки препинания
        
        Args:
            text: исходный текст
            
        Returns:
            очищенный текст
        """
        # Удаляем лишние пробелы
        if self.remove_spaces:
            text = re.sub(r'\s+', ' ', text)
        
        # Нормализуем знаки препинания
        if self.normalize_punctuation:
            # Удаляем пробелы перед знаками препинания
            text = re.sub(r'\s+([,\.;:!?])', r'\1', text)
            # Добавляем пробел после знаков препинания (если нет)
            text = re.sub(r'([,\.;:!?])([^\s])', r'\1 \2', text)
        
        # Удаляем пробелы в начале и конце
        text = text.strip()
        
        return text
    
    def clean_text_section(self, text):
        """
        Полная очистка текстового раздела
        Правильная последовательность:
        1. Удаление содержимого в скобках (структурная очистка)
        2. Удаление маркеров (удаление служебной информации)
        3. Удаление указанных символов (финальная чистка)
        4. Очистка текста (пробелы и пунктуация)
        
        Args:
            text: текст раздела
            
        Returns:
            очищенный текст
        """
        # Шаг 1: Удаляем содержимое в скобках (структурная очистка)
        if self.remove_brackets:
            text = self.remove_parentheses_content(text)
        
        # Шаг 2: Удаляем маркеры (удаление служебной информации)
        text = self.remove_number_markers(text)
        
        # Шаг 3: Удаляем указанные символы (финальная чистка)
        text = self.remove_specific_chars(text)
        
        # Шаг 4: Очищаем текст (пробелы и пунктуация)
        text = self.clean_text(text)
        
        return text
    
    def find_markers(self, text):
        """
        Находит все маркеры в тексте
        
        Args:
            text: исходный текст
            
        Returns:
            список найденных маркеров
        """
        pattern = re.compile(self.marker_pattern, re.MULTILINE)
        return list(pattern.finditer(text))
    
    def get_profile(self):
        """
        Получить текущий профиль настроек
        
        Returns:
            словарь с настройками
        """
        return {
            'marker_pattern': self.marker_pattern,
            'marker_description': self.marker_description,
            'remove_brackets': self.remove_brackets,
            'bracket_pairs': self.bracket_pairs,
            'remove_spaces': self.remove_spaces,
            'normalize_punctuation': self.normalize_punctuation,
            'chars_to_remove': self.chars_to_remove
        }
    
    def load_profile(self, profile):
        """
        Загрузить профиль настроек
        
        Args:
            profile: словарь с настройками
        """
        if 'marker_pattern' in profile:
            self.marker_pattern = profile['marker_pattern']
        if 'marker_description' in profile:
            self.marker_description = profile['marker_description']
        if 'remove_brackets' in profile:
            self.remove_brackets = profile['remove_brackets']
        if 'bracket_pairs' in profile:
            self.bracket_pairs = profile['bracket_pairs']
        if 'remove_spaces' in profile:
            self.remove_spaces = profile['remove_spaces']
        if 'normalize_punctuation' in profile:
            self.normalize_punctuation = profile['normalize_punctuation']
        if 'chars_to_remove' in profile:
            self.chars_to_remove = profile['chars_to_remove']