"""
Базовые классы для команд, связанных с управлением проектами.

Этот модуль содержит базовые классы и утилиты для работы с командами управления проектами.
"""
from typing import Any, Dict, Optional, Type, TypeVar, Generic
from dataclasses import dataclass

from core.commands.base import Command, CommandResponse, Context
from core.project.manager import ProjectManager

# Тип для параметров команды
T = TypeVar('T')

@dataclass
class ProjectCommandParams:
    """Базовый класс для параметров команд управления проектами."""
    project_id: Optional[str] = None

class ProjectCommand(Command[T], Generic[T]):
    """
    Базовый класс для команд управления проектами.
    
    Предоставляет общую функциональность для работы с проектами,
    такую как получение менеджера проектов и обработку ошибок.
    """
    
    def __init__(self, context: Optional[Context] = None):
        """
        Инициализирует команду с переданным контекстом.
        
        Args:
            context: Контекст выполнения команды (опционально)
        """
        super().__init__(context)
        self._project_manager: Optional[ProjectManager] = None
    
    @property
    def project_manager(self) -> ProjectManager:
        """
        Возвращает экземпляр менеджера проектов.
        
        Returns:
            ProjectManager: Экземпляр менеджера проектов
            
        Raises:
            RuntimeError: Если менеджер проектов не найден в контексте
        """
        if self._project_manager is not None:
            return self._project_manager
            
        if 'project_manager' in self.context:
            self._project_manager = self.context['project_manager']
            return self._project_manager
            
        # Если менеджер проектов не передан в контексте, создаем новый
        try:
            from core.project.manager import ProjectManager
            base_dir = self.context.get('base_dir')
            self._project_manager = ProjectManager(base_dir) if base_dir else ProjectManager()
            return self._project_manager
        except Exception as e:
            raise RuntimeError("Failed to initialize project manager") from e
    
    async def handle_error(self, error: Exception, params: T) -> CommandResponse:
        """
        Обрабатывает ошибки, возникающие при выполнении команды.
        
        Args:
            error: Возникшее исключение
            params: Параметры команды
            
        Returns:
            CommandResponse: Ответ с информацией об ошибке
        """
        error_type = type(error).__name__
        error_message = str(error)
        
        logger = self.context.get('logger')
        if logger:
            logger.error(f"Error in {self.__class__.__name__}: {error_message}", exc_info=True)
        
        return CommandResponse(
            success=False,
            message=f"{error_type}: {error_message}",
            data={
                'error': error_type.lower(),
                'details': error_message,
                'params': str(params)
            }
        )
    
    def get_project_id(self, params: T) -> Optional[str]:
        """
        Извлекает идентификатор проекта из параметров команды.
        
        Args:
            params: Параметры команды
            
        Returns:
            Optional[str]: Идентификатор проекта или None, если не указан
        """
        if hasattr(params, 'project_id'):
            return params.project_id
        if isinstance(params, dict):
            return params.get('project_id')
        return None
