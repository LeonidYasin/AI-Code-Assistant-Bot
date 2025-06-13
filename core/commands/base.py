"""
Базовый класс для команд.

Этот модуль содержит абстрактный базовый класс для всех команд,
а также связанные с ним исключения и вспомогательные классы.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, TypeVar, Generic, Type
from dataclasses import dataclass

# Тип для контекста выполнения команды
Context = Dict[str, Any]

# Тип для результата выполнения команды
CommandResult = Dict[str, Any]

# Тип для параметров команды
T = TypeVar('T')

class CommandError(Exception):
    """Базовое исключение для ошибок команд."""
    pass

class ValidationError(CommandError):
    """Исключение, возникающее при ошибке валидации параметров."""
    pass

class AuthorizationError(CommandError):
    """Исключение, возникающее при ошибках авторизации."""
    pass

@dataclass
class CommandResponse:
    """Результат выполнения команды."""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразует ответ команды в словарь."""
        return {
            'success': self.success,
            'message': self.message,
            'data': self.data or {}
        }

class Command(ABC, Generic[T]):
    """
    Абстрактный базовый класс для всех команд.
    
    Каждая команда должна наследоваться от этого класса и реализовывать
    метод execute().
    """
    
    name: str = ""
    description: str = ""
    
    def __init__(self, context: Optional[Context] = None):
        """
        Инициализирует команду с переданным контекстом.
        
        Args:
            context: Контекст выполнения команды (опционально)
        """
        self.context = context or {}
    
    @abstractmethod
    async def execute(self, params: T) -> CommandResponse:
        """
        Выполняет команду с переданными параметрами.
        
        Args:
            params: Параметры команды
            
        Returns:
            CommandResponse: Результат выполнения команды
            
        Raises:
            CommandError: В случае ошибки при выполнении команды
        """
        pass
    
    async def validate(self, params: T) -> None:
        """
        Проверяет валидность параметров команды.
        
        Args:
            params: Параметры команды для валидации
            
        Raises:
            ValidationError: Если параметры не прошли валидацию
        """
        pass
    
    @classmethod
    def create(cls, context: Optional[Context] = None) -> 'Command':
        """
        Фабричный метод для создания экземпляра команды.
        
        Args:
            context: Контекст выполнения команды (опционально)
            
        Returns:
            Command: Новый экземпляр команды
        """
        return cls(context)
    
    @classmethod
    def get_command_info(cls) -> Dict[str, Any]:
        """
        Возвращает информацию о команде.
        
        Returns:
            Dict[str, Any]: Словарь с информацией о команде
        """
        return {
            'name': cls.name,
            'description': cls.description,
            'params': getattr(cls, '__annotations__', {})
        }
