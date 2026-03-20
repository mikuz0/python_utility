# gui/dialogs/clone_dialog.py
import tkinter as tk
from tkinter import ttk, filedialog
import os

class CloneDialog(tk.Toplevel):
    """Диалог клонирования репозитория"""
    
    def __init__(self, parent, on_clone):
        super().__init__(parent)
        
        self.on_clone = on_clone
        self.title("Клонировать репозиторий")
        self.geometry("500x200")
        self.resizable(False, False)
        
        # Делаем модальным
        self.transient(parent)
        self.grab_set()
        
        self._create_widgets()
        
        # Центрируем относительно родителя
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (self.winfo_width() // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (self.winfo_height() // 2)
        self.geometry(f'+{x}+{y}')
    
    def _create_widgets(self):
        """Создание элементов диалога"""
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # URL
        ttk.Label(main_frame, text="URL репозитория:").pack(anchor=tk.W, pady=(0, 2))
        self.url_entry = ttk.Entry(main_frame, width=60)
        self.url_entry.pack(fill=tk.X, pady=(0, 10))
        self.url_entry.insert(0, "https://github.com/")
        self.url_entry.focus()
        
        # Папка назначения
        ttk.Label(main_frame, text="Папка назначения:").pack(anchor=tk.W, pady=(0, 2))
        path_frame = ttk.Frame(main_frame)
        path_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.path_entry = ttk.Entry(path_frame)
        self.path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.path_entry.insert(0, os.path.expanduser("~/"))
        
        ttk.Button(path_frame, text="Обзор", 
                  command=self._browse_folder).pack(side=tk.RIGHT)
        
        # Кнопки
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(button_frame, text="Клонировать", 
                  command=self._on_ok).pack(side=tk.RIGHT, padx=2)
        ttk.Button(button_frame, text="Отмена", 
                  command=self.destroy).pack(side=tk.RIGHT, padx=2)
    
    def _browse_folder(self):
        """Выбор папки"""
        folder = filedialog.askdirectory(title="Выберите папку для клонирования")
        if folder:
            self.path_entry.delete(0, tk.END)
            self.path_entry.insert(0, folder)
    
    def _on_ok(self):
        """Обработчик кнопки ОК"""
        url = self.url_entry.get().strip()
        path = self.path_entry.get().strip()
        
        if not url or not path:
            tk.messagebox.showerror("Ошибка", "Заполните все поля")
            return
        
        self.destroy()
        if self.on_clone:
            self.on_clone(url, path)