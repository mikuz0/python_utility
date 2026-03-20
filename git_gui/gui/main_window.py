# gui/main_window.py
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import logging
import os

from core.git_wrapper import GitRepo
from core.models import RepoStatus
from gui.widgets import FileListWidget, CommitAreaWidget
from gui.dialogs import CloneDialog

logger = logging.getLogger(__name__)

class GitGUI:
    """Главное окно приложения"""
    
    def __init__(self, root):
        self.root = root
        self.repo = None
        self.repo_path = None
        
        self._create_widgets()
        self._check_current_directory()
    
    def _create_widgets(self):
        """Создание интерфейса"""
        
        # Верхняя панель с кнопками
        top_frame = ttk.Frame(self.root, padding="5")
        top_frame.pack(fill=tk.X)
        
        ttk.Button(top_frame, text="📂 Открыть репозиторий", 
                  command=self.open_repository).pack(side=tk.LEFT, padx=2)
        ttk.Button(top_frame, text="📥 Клонировать", 
                  command=self.clone_repository).pack(side=tk.LEFT, padx=2)
        ttk.Button(top_frame, text="🔄 Обновить", 
                  command=self.refresh_status).pack(side=tk.LEFT, padx=2)
        
        # Информация о репозитории
        info_frame = ttk.LabelFrame(self.root, text="Информация", padding="5")
        info_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.repo_info = tk.StringVar(value="Репозиторий не открыт")
        ttk.Label(info_frame, textvariable=self.repo_info).pack(anchor=tk.W)
        
        # Ветки и действия
        branch_frame = ttk.Frame(info_frame)
        branch_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(branch_frame, text="Текущая ветка:").pack(side=tk.LEFT)
        self.branch_var = tk.StringVar(value="-")
        ttk.Label(branch_frame, textvariable=self.branch_var, 
                 font=('Arial', 10, 'bold')).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(branch_frame, text="📤 Push", 
                  command=self.push_changes).pack(side=tk.LEFT, padx=2)
        ttk.Button(branch_frame, text="📥 Pull", 
                  command=self.pull_changes).pack(side=tk.LEFT, padx=2)
        
        # Основная область с файлами
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Левая панель - измененные файлы
        left_panel = ttk.Frame(main_frame)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 2))
        
        self.changed_list = FileListWidget(left_panel, "Измененные файлы")
        self.changed_list.pack(fill=tk.BOTH, expand=True)
        
        # Кнопки для левой панели
        left_buttons = ttk.Frame(left_panel)
        left_buttons.pack(fill=tk.X, pady=5)
        
        ttk.Button(left_buttons, text="✓ Stage выбранные", 
                  command=self.stage_selected).pack(side=tk.LEFT, padx=2)
        ttk.Button(left_buttons, text="✓ Stage все", 
                  command=self.stage_all).pack(side=tk.LEFT, padx=2)
        
        # Правая панель - проиндексированные файлы
        right_panel = ttk.Frame(main_frame)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(2, 0))
        
        self.staged_list = FileListWidget(right_panel, "Проиндексировано (staged)")
        self.staged_list.pack(fill=tk.BOTH, expand=True)
        
        ttk.Button(right_panel, text="↩️ Unstage выбранные", 
                  command=self.unstage_selected).pack(pady=5)
        
        # Нижняя панель с коммитом
        self.commit_area = CommitAreaWidget(self.root, on_commit=self.commit_changes)
        self.commit_area.pack(fill=tk.X, padx=5, pady=5)
        
        # Кнопка истории
        history_btn = ttk.Button(self.commit_area, text="📋 История", 
                                command=self.show_history)
        history_btn.pack(side=tk.RIGHT, padx=2)
        
        # Статус бар
        self.status_var = tk.StringVar(value="Готов")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, 
                              relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(fill=tk.X, side=tk.BOTTOM)
    
    def _check_current_directory(self):
        """Проверка текущей директории на наличие репозитория"""
        try:
            current_dir = os.getcwd()
            repo = GitRepo(current_dir)
            self.repo = repo
            self.repo_path = current_dir
            self._update_repo_info()
            self.refresh_status()
        except:
            pass
    
    def _update_repo_info(self):
        """Обновление информации о репозитории"""
        if self.repo and self.repo.is_valid:
            self.branch_var.set(self.repo.current_branch)
            remotes = ', '.join(self.repo.remotes) if self.repo.remotes else 'нет'
            self.repo_info.set(f"Репозиторий: {self.repo_path} | Удаленные: {remotes}")
    
    def open_repository(self):
        """Открыть существующий репозиторий"""
        folder = filedialog.askdirectory(title="Выберите папку с Git репозиторием")
        if folder:
            try:
                self.repo = GitRepo(folder)
                self.repo_path = folder
                self._update_repo_info()
                self.refresh_status()
                self.status_var.set(f"Репозиторий открыт: {folder}")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось открыть репозиторий: {e}")
    
    def clone_repository(self):
        """Клонировать репозиторий"""
        def do_clone(url, path):
            try:
                self.status_var.set("Клонирование...")
                
                def clone_thread():
                    try:
                        repo = GitRepo.clone(url, path)
                        self.repo = repo
                        self.repo_path = path
                        self.root.after(0, self._update_repo_info)
                        self.root.after(0, self.refresh_status)
                        self.root.after(0, lambda: self.status_var.set("Клонирование завершено"))
                    except Exception as e:
                        self.root.after(0, lambda: messagebox.showerror("Ошибка", str(e)))
                        self.root.after(0, lambda: self.status_var.set("Ошибка клонирования"))
                
                thread = threading.Thread(target=clone_thread)
                thread.start()
                
            except Exception as e:
                messagebox.showerror("Ошибка", str(e))
        
        CloneDialog(self.root, do_clone)
    
    def refresh_status(self):
        """Обновить статус файлов"""
        if not self.repo or not self.repo.is_valid:
            self.status_var.set("Репозиторий не открыт")
            return
        
        try:
            status = self.repo.get_status()
            
            # Обновляем списки файлов
            self.changed_list.set_files(
                status.untracked + status.modified + status.deleted + status.renamed
            )
            self.staged_list.set_files(status.staged)
            
            self.status_var.set(
                f"Изменено: {status.total_changed}, Проиндексировано: {len(status.staged)}"
            )
            
        except Exception as e:
            self.status_var.set(f"Ошибка: {e}")
            logger.error(f"Ошибка обновления статуса: {e}")
    
    def stage_selected(self):
        """Добавить выбранные файлы в индекс"""
        if not self.repo:
            return
        
        selected = self.changed_list.get_selected_files()
        if not selected:
            messagebox.showinfo("Информация", "Выберите файлы для добавления")
            return
        
        files = [f.path for f in selected]
        if self.repo.stage_files(files):
            self.refresh_status()
            self.status_var.set(f"Добавлено в индекс: {len(files)} файлов")
    
    def stage_all(self):
        """Добавить все измененные файлы в индекс"""
        if not self.repo:
            return
        
        all_files = [f.path for f in self.changed_list.files]
        if self.repo.stage_files(all_files):
            self.refresh_status()
            self.status_var.set("Все файлы добавлены в индекс")
    
    def unstage_selected(self):
        """Убрать файлы из индекса"""
        if not self.repo:
            return
        
        selected = self.staged_list.get_selected_files()
        if not selected:
            messagebox.showinfo("Информация", "Выберите файлы для отмены индексации")
            return
        
        files = [f.path for f in selected]
        if self.repo.unstage_files(files):
            self.refresh_status()
            self.status_var.set(f"Убрано из индекса: {len(files)} файлов")
    
    def commit_changes(self):
        """Сделать коммит"""
        if not self.repo:
            return
        
        message = self.commit_area.get_message()
        if not message:
            messagebox.showwarning("Предупреждение", "Введите сообщение коммита")
            return
        
        status = self.repo.get_status()
        if not status.has_changes:
            messagebox.showinfo("Информация", "Нет изменений для коммита")
            return
        
        if self.repo.commit(message):
            self.commit_area.clear()
            self.refresh_status()
            self.status_var.set("Коммит создан успешно")
    
    def push_changes(self):
        """Отправить изменения на удаленный репозиторий"""
        if not self.repo:
            return
        
        if not self.repo.remotes:
            messagebox.showinfo("Информация", "Нет настроенных удаленных репозиториев")
            return
        
        def push_thread():
            if self.repo.push():
                self.root.after(0, lambda: self.status_var.set("Изменения отправлены"))
                self.root.after(0, self.refresh_status)
            else:
                self.root.after(0, lambda: messagebox.showerror("Ошибка", "Не удалось отправить изменения"))
        
        thread = threading.Thread(target=push_thread)
        thread.start()
        self.status_var.set("Отправка изменений...")
    
    def pull_changes(self):
        """Получить изменения с удаленного репозитория"""
        if not self.repo:
            return
        
        if not self.repo.remotes:
            messagebox.showinfo("Информация", "Нет настроенных удаленных репозиториев")
            return
        
        def pull_thread():
            if self.repo.pull():
                self.root.after(0, lambda: self.status_var.set("Изменения получены"))
                self.root.after(0, self.refresh_status)
            else:
                self.root.after(0, lambda: messagebox.showerror("Ошибка", "Не удалось получить изменения"))
        
        thread = threading.Thread(target=pull_thread)
        thread.start()
        self.status_var.set("Получение изменений...")
    
    def show_history(self):
        """Показать историю коммитов"""
        if not self.repo:
            return
        
        history_window = tk.Toplevel(self.root)
        history_window.title("История коммитов")
        history_window.geometry("600x400")
        
        from tkinter import scrolledtext
        text_area = scrolledtext.ScrolledText(history_window, wrap=tk.WORD)
        text_area.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        commits = self.repo.get_commits()
        for commit in commits:
            text_area.insert(tk.END, f"Коммит: {commit.short_sha}\n")
            text_area.insert(tk.END, f"Автор: {commit.author}\n")
            text_area.insert(tk.END, f"Дата: {commit.date}\n")
            text_area.insert(tk.END, f"Сообщение: {commit.message}\n")
            text_area.insert(tk.END, "-" * 50 + "\n\n")
        
        text_area.configure(state='disabled')