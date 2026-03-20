# core/models.py
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

@dataclass
class FileStatus:
    """Статус одного файла"""
    path: str
    status: str  # 'untracked', 'modified', 'deleted', 'staged', 'renamed'
    old_path: Optional[str] = None  # для переименованных файлов
    
    @property
    def icon(self) -> str:
        """Иконка для статуса"""
        icons = {
            'untracked': '❓',
            'modified': '📝',
            'deleted': '🗑️',
            'staged': '✓',
            'renamed': '📎'
        }
        return icons.get(self.status, '📄')
    
    @property
    def color(self) -> str:
        """Цвет для отображения"""
        colors = {
            'untracked': 'gray',
            'modified': 'blue',
            'deleted': 'red',
            'staged': 'green',
            'renamed': 'purple'
        }
        return colors.get(self.status, 'black')

@dataclass
class CommitInfo:
    """Информация о коммите"""
    hexsha: str
    author: str
    date: datetime
    message: str
    
    @property
    def short_sha(self) -> str:
        """Короткий хеш (первые 7 символов)"""
        return self.hexsha[:7]

@dataclass
class RepoStatus:
    """Полный статус репозитория"""
    untracked: List[FileStatus] = None
    modified: List[FileStatus] = None
    deleted: List[FileStatus] = None
    staged: List[FileStatus] = None
    renamed: List[FileStatus] = None
    
    def __post_init__(self):
        self.untracked = self.untracked or []
        self.modified = self.modified or []
        self.deleted = self.deleted or []
        self.staged = self.staged or []
        self.renamed = self.renamed or []
    
    @property
    def total_changed(self) -> int:
        """Общее количество измененных файлов"""
        return len(self.untracked) + len(self.modified) + \
               len(self.deleted) + len(self.renamed)
    
    @property
    def has_changes(self) -> bool:
        """Есть ли какие-то изменения"""
        return self.total_changed > 0 or len(self.staged) > 0