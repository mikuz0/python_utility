# gui/main_window.py
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import logging
import os
import git

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
                error_msg = str(e)
                messagebox.showerror("Ошибка", f"Не удалось открыть репозиторий: {error_msg}")
    
    def extract_repo_name(self, url):
        """Извлекает имя репозитория из URL"""
        # Убираем .git в конце, если есть
        url = url.rstrip('/')
        if url.endswith('.git'):
            url = url[:-4]
        
        # Берем последнюю часть URL
        parts = url.split('/')
        if parts:
            repo_name = parts[-1]
            # Проверяем, что имя не пустое и не похоже на URL
            if repo_name and not repo_name.startswith('http'):
                return repo_name
        return None
    
    def clone_repository(self):
        """Клонировать репозиторий"""
        clone_window = tk.Toplevel(self.root)
        clone_window.title("Клонировать репозиторий")
        clone_window.geometry("600x300")
        clone_window.resizable(False, False)
        
        # Делаем модальным
        clone_window.transient(self.root)
        clone_window.grab_set()
        
        main_frame = ttk.Frame(clone_window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # URL
        ttk.Label(main_frame, text="URL репозитория:").pack(anchor=tk.W, pady=(0, 2))
        url_entry = ttk.Entry(main_frame, width=70)
        url_entry.pack(fill=tk.X, pady=(0, 10))
        url_entry.insert(0, "https://github.com/")
        url_entry.focus()
        
        # Папка назначения (родительская папка)
        ttk.Label(main_frame, text="Родительская папка:").pack(anchor=tk.W, pady=(0, 2))
        path_frame = ttk.Frame(main_frame)
        path_frame.pack(fill=tk.X, pady=(0, 5))
        
        path_entry = ttk.Entry(path_frame, width=50)
        path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        # Предлагаем папку по умолчанию
        default_path = os.path.join(os.path.expanduser("~"), "src")
        path_entry.insert(0, default_path)
        
        def browse_folder():
            folder = filedialog.askdirectory(
                title="Выберите родительскую папку для клонирования",
                initialdir=path_entry.get() or os.path.expanduser("~")
            )
            if folder:
                path_entry.delete(0, tk.END)
                path_entry.insert(0, folder)
                update_info()
        
        ttk.Button(path_frame, text="Обзор", command=browse_folder).pack(side=tk.RIGHT)
        
        # Информация о том, как будет создана папка
        info_label = ttk.Label(main_frame, text="", foreground="gray", wraplength=550)
        info_label.pack(fill=tk.X, pady=5)
        
        def update_info(*args):
            """Обновляет информационную строку о том, куда будет клонировано"""
            url = url_entry.get().strip()
            parent_path = path_entry.get().strip()
            
            if url and parent_path:
                # Извлекаем имя репозитория из URL
                repo_name = self.extract_repo_name(url)
                if repo_name:
                    full_path = os.path.join(parent_path, repo_name)
                    info_label.config(text=f"📁 Будет создана папка: {full_path}")
                else:
                    info_label.config(text="⚠️ Не удалось определить имя репозитория из URL")
            else:
                info_label.config(text="")
        
        # Привязываем обновление информации к вводу
        url_entry.bind('<KeyRelease>', lambda e: update_info())
        path_entry.bind('<KeyRelease>', lambda e: update_info())
        
        # Статус
        status_label = ttk.Label(main_frame, text="", foreground="gray")
        status_label.pack(fill=tk.X, pady=5)
        
        def do_clone():
            url = url_entry.get().strip()
            parent_path = path_entry.get().strip()
            
            if not url or not parent_path:
                messagebox.showerror("Ошибка", "Заполните все поля")
                return
            
            # Извлекаем имя репозитория
            repo_name = self.extract_repo_name(url)
            if not repo_name:
                messagebox.showerror("Ошибка", "Не удалось определить имя репозитория из URL")
                return
            
            # Формируем полный путь для клонирования
            full_path = os.path.join(parent_path, repo_name)
            
            # Проверяем, существует ли уже такая папка
            if os.path.exists(full_path):
                if os.path.isdir(full_path) and os.listdir(full_path):
                    result = messagebox.askyesno(
                        "Папка уже существует",
                        f"Папка '{full_path}' уже существует и не пуста.\n\n"
                        "Хотите открыть этот репозиторий вместо клонирования?"
                    )
                    if result:
                        # Открываем существующий репозиторий
                        try:
                            self.repo = GitRepo(full_path)
                            self.repo_path = full_path
                            self._update_repo_info()
                            self.refresh_status()
                            self.status_var.set(f"Репозиторий открыт: {full_path}")
                            clone_window.destroy()
                        except Exception as e:
                            error_msg = str(e)
                            messagebox.showerror("Ошибка", f"Не удалось открыть репозиторий: {error_msg}")
                    return
            
            clone_window.destroy()
            
            def clone_thread():
                try:
                    self.root.after(0, lambda: self.status_var.set(f"Клонирование в {full_path}..."))
                    
                    # Клонируем
                    repo = git.Repo.clone_from(url, full_path)
                    
                    # Сохраняем репозиторий
                    self.repo = GitRepo(full_path)
                    self.repo_path = full_path
                    
                    # Успех
                    self.root.after(0, self._update_repo_info)
                    self.root.after(0, self.refresh_status)
                    self.root.after(0, lambda: self.status_var.set(f"Клонировано: {full_path}"))
                    self.root.after(0, lambda: messagebox.showinfo(
                        "Успех", 
                        f"Репозиторий '{repo_name}' склонирован в:\n{full_path}"
                    ))
                    
                except Exception as e:
                    error_msg = str(e)
                    self.root.after(0, lambda: self.status_var.set("Ошибка клонирования"))
                    self.root.after(0, lambda msg=error_msg: messagebox.showerror(
                        "Ошибка клонирования", 
                        f"{msg}\n\nURL: {url}\nПапка: {full_path}"
                    ))
            
            thread = threading.Thread(target=clone_thread)
            thread.start()
        
        # Кнопки
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(button_frame, text="Клонировать", command=do_clone).pack(side=tk.RIGHT, padx=2)
        ttk.Button(button_frame, text="Отмена", command=clone_window.destroy).pack(side=tk.RIGHT, padx=2)
        
        # Инициализируем информацию
        update_info()
    
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
            error_msg = str(e)
            self.status_var.set(f"Ошибка: {error_msg}")
            logger.error(f"Ошибка обновления статуса: {error_msg}")
    
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
        else:
            messagebox.showerror("Ошибка", "Не удалось добавить файлы в индекс")
    
    def stage_all(self):
        """Добавить все измененные файлы в индекс"""
        if not self.repo:
            return
        
        all_files = [f.path for f in self.changed_list.files]
        if self.repo.stage_files(all_files):
            self.refresh_status()
            self.status_var.set("Все файлы добавлены в индекс")
        else:
            messagebox.showerror("Ошибка", "Не удалось добавить файлы в индекс")
    
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
        else:
            messagebox.showerror("Ошибка", "Не удалось убрать файлы из индекса")
    
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
        else:
            messagebox.showerror("Ошибка", "Не удалось создать коммит")
    
    def push_changes(self):
        """Отправить изменения на удаленный репозиторий"""
        if not self.repo:
            return
        
        if not self.repo.remotes:
            messagebox.showinfo("Информация", "Нет настроенных удаленных репозиториев")
            return
        
        def push_thread():
            try:
                if self.repo.push():
                    self.root.after(0, lambda: self.status_var.set("Изменения отправлены"))
                    self.root.after(0, self.refresh_status)
                else:
                    self.root.after(0, lambda: messagebox.showerror(
                        "Ошибка", 
                        "Не удалось отправить изменения\n\n"
                        "Проверьте подключение к интернету и настройки удаленного репозитория"
                    ))
            except Exception as e:
                error_msg = str(e)
                self.root.after(0, lambda msg=error_msg: messagebox.showerror("Ошибка push", msg))
        
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
            try:
                if self.repo.pull():
                    self.root.after(0, lambda: self.status_var.set("Изменения получены"))
                    self.root.after(0, self.refresh_status)
                else:
                    self.root.after(0, lambda: messagebox.showerror(
                        "Ошибка", 
                        "Не удалось получить изменения\n\n"
                        "Проверьте подключение к интернету"
                    ))
            except Exception as e:
                error_msg = str(e)
                self.root.after(0, lambda msg=error_msg: messagebox.showerror("Ошибка pull", msg))
        
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
        
        # Делаем модальным
        history_window.transient(self.root)
        
        from tkinter import scrolledtext
        text_area = scrolledtext.ScrolledText(history_window, wrap=tk.WORD)
        text_area.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        commits = self.repo.get_commits()
        if commits:
            for commit in commits:
                text_area.insert(tk.END, f"Коммит: {commit.short_sha}\n")
                text_area.insert(tk.END, f"Автор: {commit.author}\n")
                text_area.insert(tk.END, f"Дата: {commit.date}\n")
                text_area.insert(tk.END, f"Сообщение: {commit.message}\n")
                text_area.insert(tk.END, "-" * 50 + "\n\n")
        else:
            text_area.insert(tk.END, "Нет коммитов в этом репозитории")
        
        text_area.configure(state='disabled')