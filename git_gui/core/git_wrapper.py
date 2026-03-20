# core/git_wrapper.py
import git
import logging
from pathlib import Path
from typing import Optional, List
from .models import FileStatus, CommitInfo, RepoStatus

logger = logging.getLogger(__name__)

class GitRepo:
    """Обертка для работы с Git репозиторием"""
    
    def __init__(self, path: str):
        """
        Инициализация репозитория
        
        Args:
            path: путь к Git репозиторию
        """
        self.path = Path(path)
        self.repo = git.Repo(path)
        logger.info(f"Открыт репозиторий: {path}")
    
    @property
    def is_valid(self) -> bool:
        """Проверка валидности репозитория"""
        try:
            return self.repo is not None and not self.repo.bare
        except:
            return False
    
    @property
    def current_branch(self) -> str:
        """Текущая ветка"""
        try:
            return self.repo.active_branch.name
        except:
            return "(detached HEAD)"
    
    @property
    def remotes(self) -> List[str]:
        """Список удаленных репозиториев"""
        return [remote.name for remote in self.repo.remotes]
    
    def is_first_commit(self) -> bool:
        """Проверка, есть ли хотя бы один коммит"""
        try:
            self.repo.head.commit
            return False
        except ValueError:
            return True
    
    def get_status(self) -> RepoStatus:
        """Получение статуса репозитория"""
        status = RepoStatus()
        
        try:
            # Неотслеживаемые файлы
            for file in self.repo.untracked_files:
                status.untracked.append(FileStatus(file, 'untracked'))
            
            # Изменения в рабочей директории
            diff = self.repo.index.diff(None)
            for item in diff:
                if item.change_type == 'D':
                    status.deleted.append(FileStatus(item.b_path, 'deleted'))
                elif item.change_type == 'R':
                    status.renamed.append(FileStatus(
                        item.rename_to, 'renamed', 
                        old_path=item.rename_from
                    ))
                else:
                    status.modified.append(FileStatus(item.b_path, 'modified'))
            
            # Проиндексированные изменения
            if not self.is_first_commit():
                staged = self.repo.index.diff('HEAD')
                for item in staged:
                    status.staged.append(FileStatus(item.b_path, 'staged'))
            else:
                # Для первого коммита
                for path in self.repo.index.entries:
                    status.staged.append(FileStatus(path, 'staged'))
            
            logger.debug(f"Статус получен: {status.total_changed} изменений, {len(status.staged)} в индексе")
            
        except Exception as e:
            logger.error(f"Ошибка получения статуса: {e}")
        
        return status
    
    def stage_files(self, files: List[str]) -> bool:
        """
        Добавить файлы в индекс
        
        Args:
            files: список файлов для добавления
            
        Returns:
            bool: успешно ли выполнено
        """
        try:
            self.repo.index.add(files)
            logger.info(f"Добавлены в индекс: {files}")
            return True
        except Exception as e:
            logger.error(f"Ошибка добавления в индекс: {e}")
            return False
    
    def unstage_files(self, files: List[str]) -> bool:
        """
        Убрать файлы из индекса
        
        Args:
            files: список файлов для удаления из индекса
            
        Returns:
            bool: успешно ли выполнено
        """
        try:
            self.repo.index.remove(files, working_tree=True)
            logger.info(f"Убраны из индекса: {files}")
            return True
        except Exception as e:
            logger.error(f"Ошибка удаления из индекса: {e}")
            return False
    
    def commit(self, message: str) -> bool:
        """
        Создать коммит
        
        Args:
            message: сообщение коммита
            
        Returns:
            bool: успешно ли выполнен коммит
        """
        try:
            self.repo.index.commit(message)
            logger.info(f"Коммит создан: {message[:50]}...")
            return True
        except Exception as e:
            logger.error(f"Ошибка создания коммита: {e}")
            return False
    
    def push(self, remote: str = 'origin', branch: str = None) -> bool:
        """
        Отправить изменения на удаленный репозиторий
        
        Args:
            remote: имя удаленного репозитория
            branch: ветка для отправки (если None - текущая)
            
        Returns:
            bool: успешно ли выполнено
        """
        try:
            if not self.repo.remotes:
                logger.error("Нет удаленных репозиториев")
                return False
            
            if branch is None:
                branch = self.current_branch
            
            remote_obj = getattr(self.repo.remotes, remote)
            remote_obj.push(branch)
            logger.info(f"Push выполнен: {remote}/{branch}")
            return True
        except Exception as e:
            logger.error(f"Ошибка push: {e}")
            return False
    
    def pull(self, remote: str = 'origin', branch: str = None) -> bool:
        """
        Получить изменения с удаленного репозитория
        
        Args:
            remote: имя удаленного репозитория
            branch: ветка для получения (если None - текущая)
            
        Returns:
            bool: успешно ли выполнено
        """
        try:
            if not self.repo.remotes:
                logger.error("Нет удаленных репозиториев")
                return False
            
            if branch is None:
                branch = self.current_branch
            
            remote_obj = getattr(self.repo.remotes, remote)
            remote_obj.pull(branch)
            logger.info(f"Pull выполнен: {remote}/{branch}")
            return True
        except Exception as e:
            logger.error(f"Ошибка pull: {e}")
            return False
    
    def get_commits(self, max_count: int = 50) -> List[CommitInfo]:
        """
        Получить историю коммитов
        
        Args:
            max_count: максимальное количество коммитов
            
        Returns:
            List[CommitInfo]: список коммитов
        """
        commits = []
        try:
            for commit in self.repo.iter_commits(max_count=max_count):
                commits.append(CommitInfo(
                    hexsha=commit.hexsha,
                    author=str(commit.author),
                    date=commit.committed_datetime,
                    message=commit.message.strip()
                ))
        except Exception as e:
            logger.error(f"Ошибка получения истории: {e}")
        
        return commits
    
    @classmethod
    def clone(cls, url: str, path: str) -> 'GitRepo':
        """
        Клонировать репозиторий
        
        Args:
            url: URL репозитория
            path: путь для клонирования
            
        Returns:
            GitRepo: объект репозитория
        """
        try:
            repo = git.Repo.clone_from(url, path)
            logger.info(f"Репозиторий склонирован: {url} -> {path}")
            return cls(path)
        except Exception as e:
            logger.error(f"Ошибка клонирования: {e}")
            raise