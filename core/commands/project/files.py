"""
Команды для работы с файлами проектов.

Этот модуль содержит команды для управления файлами в проектах,
такие как создание, чтение, обновление и удаление файлов.
"""
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

from ..base import Command, CommandResponse, Context
from .base import ProjectCommand, ProjectCommandParams

logger = logging.getLogger(__name__)

@dataclass
class FileOperationParams(ProjectCommandParams):
    """Базовые параметры для операций с файлами."""
    file_path: str
    content: Optional[str] = None
    encoding: str = "utf-8"

@dataclass
class CreateFileParams(FileOperationParams):
    """Параметры команды создания файла."""
    overwrite: bool = False

class CreateFileCommand(ProjectCommand[CreateFileParams]):
    """
    Команда создания нового файла в проекте.
    
    Создает новый файл с указанным содержимым в проекте.
    """
    
    name = "create_file"
    description = "Создает новый файл в проекте"
    
    async def execute(self, params: CreateFileParams) -> CommandResponse:
        """
        Выполняет создание файла.
        
        Args:
            params: Параметры команды
            
        Returns:
            CommandResponse: Результат выполнения команды
        """
        try:
            project_id = self.get_project_id(params)
            project = await self.project_manager.get_project(project_id) if project_id else None
            
            file_path = Path(params.file_path)
            
            # Если путь абсолютный, используем его, иначе относительный к проекту
            if not file_path.is_absolute() and project:
                file_path = project.path / file_path
            
            logger.info(f"Creating file: {file_path}")
            
            # Проверяем существование файла
            if file_path.exists() and not params.overwrite:
                return CommandResponse(
                    success=False,
                    message=f"File already exists: {file_path}",
                    data={
                        'error': 'file_exists',
                        'path': str(file_path)
                    }
                )
            
            # Создаем директорию, если её нет
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Записываем содержимое файла
            with open(file_path, 'w', encoding=params.encoding) as f:
                if params.content is not None:
                    f.write(params.content)
            
            return CommandResponse(
                success=True,
                message=f"File created: {file_path}",
                data={
                    'path': str(file_path),
                    'project_id': project.id if project else None
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to create file: {str(e)}", exc_info=True)
            return CommandResponse(
                success=False,
                message=f"Failed to create file: {str(e)}",
                data={
                    'error': 'file_creation_failed',
                    'details': str(e)
                }
            )

@dataclass
class ReadFileParams(FileOperationParams):
    """Параметры команды чтения файла."""
    start_line: Optional[int] = None
    end_line: Optional[int] = None

class ReadFileCommand(ProjectCommand[ReadFileParams]):
    """
    Команда чтения содержимого файла из проекта.
    
    Читает содержимое файла и возвращает его с возможностью
    указания диапазона строк.
    """
    
    name = "read_file"
    description = "Читает содержимое файла из проекта"
    
    async def execute(self, params: ReadFileParams) -> CommandResponse:
        """
        Выполняет чтение файла.
        
        Args:
            params: Параметры команды
            
        Returns:
            CommandResponse: Результат выполнения команды с содержимым файла
        """
        try:
            project_id = self.get_project_id(params)
            project = await self.project_manager.get_project(project_id) if project_id else None
            
            file_path = Path(params.file_path)
            
            # Если путь не абсолютный и есть проект, используем путь относительно проекта
            if not file_path.is_absolute() and project:
                file_path = project.path / file_path
            
            logger.info(f"Reading file: {file_path}")
            
            # Проверяем существование файла
            if not file_path.exists() or not file_path.is_file():
                return CommandResponse(
                    success=False,
                    message=f"File not found: {file_path}",
                    data={
                        'error': 'file_not_found',
                        'path': str(file_path)
                    }
                )
            
            # Читаем содержимое файла
            with open(file_path, 'r', encoding=params.encoding) as f:
                lines = f.readlines()
            
            # Применяем фильтрацию по строкам, если указаны границы
            if params.start_line is not None or params.end_line is not None:
                start = params.start_line or 0
                end = (params.end_line + 1) if params.end_line is not None else None
                lines = lines[start:end]
            
            content = ''.join(lines)
            
            return CommandResponse(
                success=True,
                message=f"File read: {file_path}",
                data={
                    'content': content,
                    'path': str(file_path),
                    'line_count': len(lines),
                    'project_id': project.id if project else None
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to read file: {str(e)}", exc_info=True)
            return CommandResponse(
                success=False,
                message=f"Failed to read file: {str(e)}",
                data={
                    'error': 'file_read_failed',
                    'details': str(e)
                }
            )

@dataclass
class ListFilesParams(ProjectCommandParams):
    """Параметры команды списка файлов."""
    directory: str = "."
    recursive: bool = False
    pattern: Optional[str] = None

class ListFilesCommand(ProjectCommand[ListFilesParams]):
    """
    Команда получения списка файлов в директории проекта.
    
    Возвращает список файлов и поддиректорий в указанной директории
    с возможностью рекурсивного обхода и фильтрации по шаблону.
    """
    
    name = "list_files"
    description = "Возвращает список файлов в указанной директории проекта"
    
    async def execute(self, params: ListFilesParams) -> CommandResponse:
        """
        Выполняет получение списка файлов.
        
        Args:
            params: Параметры команды
            
        Returns:
            CommandResponse: Результат выполнения команды со списком файлов
        """
        try:
            project_id = self.get_project_id(params)
            project = await self.project_manager.get_project(project_id) if project_id else None
            
            base_dir = Path(params.directory)
            
            # Если путь не абсолютный и есть проект, используем путь относительно проекта
            if not base_dir.is_absolute() and project:
                base_dir = project.path / base_dir
            
            logger.info(f"Listing files in: {base_dir}")
            
            # Проверяем существование директории
            if not base_dir.exists() or not base_dir.is_dir():
                return CommandResponse(
                    success=False,
                    message=f"Directory not found: {base_dir}",
                    data={
                        'error': 'directory_not_found',
                        'path': str(base_dir)
                    }
                )
            
            # Получаем список файлов
            files = []
            pattern = params.pattern or "*"
            
            if params.recursive:
                file_paths = list(base_dir.rglob(pattern))
            else:
                file_paths = list(base_dir.glob(pattern))
            
            for file_path in file_paths:
                try:
                    if file_path.is_file():
                        stat = file_path.stat()
                        files.append({
                            'name': file_path.name,
                            'path': str(file_path.relative_to(base_dir)),
                            'absolute_path': str(file_path),
                            'size': stat.st_size,
                            'modified': stat.st_mtime,
                            'is_dir': False
                        })
                    elif file_path.is_dir():
                        stat = file_path.stat()
                        files.append({
                            'name': file_path.name,
                            'path': str(file_path.relative_to(base_dir)),
                            'absolute_path': str(file_path),
                            'size': 0,
                            'modified': stat.st_mtime,
                            'is_dir': True
                        })
                except Exception as e:
                    logger.warning(f"Error processing {file_path}: {str(e)}")
            
            return CommandResponse(
                success=True,
                message=f"Found {len(files)} items in {base_dir}",
                data={
                    'files': files,
                    'directory': str(base_dir),
                    'project_id': project.id if project else None
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to list files: {str(e)}", exc_info=True)
            return CommandResponse(
                success=False,
                message=f"Failed to list files: {str(e)}",
                data={
                    'error': 'list_files_failed',
                    'details': str(e)
                }
            )
