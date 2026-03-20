# gui/widgets/commit_area.py
import tkinter as tk
from tkinter import ttk, scrolledtext
from typing import Callable

class CommitAreaWidget(ttk.Frame):
    """Виджет для создания коммита"""
    
    def __init__(self, parent, on_commit: Callable = None, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.on_commit = on_commit
        
        # Заголовок
        title_label = ttk.Label(self, text="Сообщение коммита", 
                                font=('Arial', 10, 'bold'))
        title_label.pack(anchor=tk.W)
        
        # Поле для ввода сообщения
        self.message_text = scrolledtext.ScrolledText(self, height=4, wrap=tk.WORD)
        self.message_text.pack(fill=tk.X, pady=5)
        
        # Кнопка коммита
        button_frame = ttk.Frame(self)
        button_frame.pack(fill=tk.X)
        
        self.commit_btn = ttk.Button(button_frame, text="💾 Сделать коммит", 
                                     command=self._on_commit_click)
        self.commit_btn.pack(side=tk.LEFT, padx=2)
        
        # Статус
        self.status_label = ttk.Label(button_frame, text="", foreground="gray")
        self.status_label.pack(side=tk.LEFT, padx=10)
    
    def get_message(self) -> str:
        """Получить сообщение коммита"""
        return self.message_text.get("1.0", tk.END).strip()
    
    def clear(self):
        """Очистить поле ввода"""
        self.message_text.delete("1.0", tk.END)
    
    def set_status(self, text: str, is_error: bool = False):
        """Установить статус"""
        self.status_label.config(text=text, 
                                foreground="red" if is_error else "gray")
    
    def _on_commit_click(self):
        """Обработчик кнопки коммита"""
        if self.on_commit:
            self.on_commit()
    
    def enable(self):
        """Включить виджет"""
        self.message_text.config(state=tk.NORMAL)
        self.commit_btn.config(state=tk.NORMAL)
    
    def disable(self):
        """Отключить виджет"""
        self.message_text.config(state=tk.DISABLED)
        self.commit_btn.config(state=tk.DISABLED)