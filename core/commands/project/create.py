"""
Команды для создания и настройки проектов.

Этот модуль содержит команды для работы с созданием и настройкой проектов.
"""
import logging
from typing import Any, Dict, Optional
from dataclasses import dataclass

from ..base import Command, CommandResponse, Context
from .base import ProjectCommand, ProjectCommandParams

logger = logging.getLogger(__name__)

@dataclass
class CreateProjectParams(ProjectCommandParams):
    """Параметры команды создания проекта."""
    project_name: str
    description: Optional[str] = None
    template: Optional[str] = None
    path: Optional[str] = None

class CreateProjectCommand(ProjectCommand[CreateProjectParams]):
    """
    Команда создания нового проекта.
    
    Создает новую директорию проекта и инициализирует необходимые файлы.
    """
    
    name = "create_project"
    description = "Создает новый проект с указанным именем и опциональным шаблоном"
    
    async def execute(self, params: CreateProjectParams) -> CommandResponse:
        """
        Выполняет создание проекта.
        
        Args:
            params: Параметры команды
            
        Returns:
            CommandResponse: Результат выполнения команды
        """
        try:
            logger.info(f"Creating project: {params.project_name}")
            
            # Создаем проект
            project = await self.project_manager.create_project(
                name=params.project_name,
                description=params.description,
                template=params.template,
                path=params.path
            )
            
            return CommandResponse(
                success=True,
                message=f"Project '{params.project_name}' created successfully",
                data={
                    'project_id': project.id,
                    'project_name': project.name,
                    'path': str(project.path)
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to create project: {str(e)}", exc_info=True)
            return CommandResponse(
                success=False,
                message=f"Failed to create project: {str(e)}",
                data={
                    'error': 'project_creation_failed',
                    'details': str(e)
                }
            )

@dataclass
class InitProjectParams(ProjectCommandParams):
    """Параметры команды инициализации проекта."""
    project_name: Optional[str] = None
    description: Optional[str] = None
    template: Optional[str] = None

class InitProjectCommand(ProjectCommand[InitProjectParams]):
    """
    Команда инициализации существующей директории как проекта.
    
    Инициализирует текущую директорию как проект, создавая необходимые конфигурационные файлы.
    """
    
    name = "init_project"
    description = "Инициализирует текущую директорию как проект"
    
    async def execute(self, params: InitProjectParams) -> CommandResponse:
        """
        Выполняет инициализацию проекта.
        
        Args:
            params: Параметры команды
            
        Returns:
            CommandResponse: Результат выполнения команды
        """
        try:
            logger.info("Initializing project")
            
            # Инициализируем проект
            project = await self.project_manager.init_project(
                name=params.project_name,
                description=params.description,
                template=params.template
            )
            
            return CommandResponse(
                success=True,
                message=f"Project '{project.name}' initialized successfully",
                data={
                    'project_id': project.id,
                    'project_name': project.name,
                    'path': str(project.path)
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to initialize project: {str(e)}", exc_info=True)
            return CommandResponse(
                success=False,
                message=f"Failed to initialize project: {str(e)}",
                data={
                    'error': 'project_init_failed',
                    'details': str(e)
                }
            )
