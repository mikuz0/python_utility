#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import tkinter as tk
import sys
import os

# Добавляем путь к проекту
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gui.main_window import GitGUI

def main():
    """Главная функция запуска приложения"""
    root = tk.Tk()
    root.title("Git GUI")
    root.geometry("900x700")
    
    # Устанавливаем иконку (если есть)
    try:
        root.iconbitmap(default="assets/icon.ico")
    except:
        pass
    
    app = GitGUI(root)
    
    # Центрируем окно
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f'{width}x{height}+{x}+{y}')
    
    root.mainloop()

if __name__ == "__main__":
    main()