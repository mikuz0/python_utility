#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Книги в аудио - Графическое приложение для конвертации книг в аудиофайлы
С использованием локальных нейросетей
"""

import tkinter as tk
import sys
import os

# Добавляем текущую директорию в путь для импорта
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gui_app import BookToAudioGUI

def main():
    """Точка входа в приложение"""
    root = tk.Tk()
    app = BookToAudioGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()