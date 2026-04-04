# gui/widgets/file_list.py
import tkinter as tk
from tkinter import ttk
from typing import Callable, List
from core.models import FileStatus

class FileListWidget(ttk.Frame):
    """Виджет для отображения списка файлов с иконками статуса"""
    
    def __init__(self, parent, title: str, on_select: Callable = None, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.on_select = on_select
        self.files = []  # список FileStatus объектов
        
        # Заголовок
        title_label = ttk.Label(self, text=title, font=('Arial', 10, 'bold'))
        title_label.pack(anchor=tk.W, pady=(0, 2))
        
        # Список с прокруткой
        frame = ttk.Frame(self)
        frame.pack(fill=tk.BOTH, expand=True)
        
        self.listbox = tk.Listbox(frame, height=10)
        scrollbar = ttk.Scrollbar(frame, orient="vertical", 
                                  command=self.listbox.yview)
        self.listbox.configure(yscrollcommand=scrollbar.set)
        
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Привязка события выбора
        self.listbox.bind('<<ListboxSelect>>', self._on_select)
    
    def set_files(self, files: List[FileStatus]):
        """Установить список файлов"""
        self.files = files
        self.refresh()
    
    def refresh(self):
        """Обновить отображение"""
        self.listbox.delete(0, tk.END)
        
        for file in self.files:
            # Добавляем индикатор для удаленных файлов
            if file.status == 'deleted':
                display_text = f"{file.icon} {file.path} [УДАЛЕН]"
            else:
                display_text = f"{file.icon} {file.path}"
            
            self.listbox.insert(tk.END, display_text)
            self.listbox.itemconfig(tk.END, fg=file.color)
    
    def get_selected_files(self) -> List[FileStatus]:
        """Получить выбранные файлы"""
        selection = self.listbox.curselection()
        return [self.files[i] for i in selection]
    
    def _on_select(self, event):
        """Обработчик выбора файла"""
        if self.on_select:
            self.on_select(self.get_selected_files())
    
    def clear_selection(self):
        """Снять выделение"""
        self.listbox.selection_clear(0, tk.END)