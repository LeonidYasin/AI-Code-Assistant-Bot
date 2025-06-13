"""
Диспетчер команд.

Этот модуль содержит класс Dispatcher, который отвечает за маршрутизацию
и выполнение команд.
"""
import logging
from typing import Dict, Type, Any, Optional, TypeVar, Generic, Callable, Awaitable
from functools import wraps

from .base import Command, CommandResponse, CommandError, ValidationError, Context

logger = logging.getLogger(__name__)

# Тип для middleware
Middleware = Callable[[Command, Context], Awaitable[None]]

class CommandDispatcher:
    """
    Диспетчер команд, отвечающий за маршрутизацию и выполнение команд.
    """
    
    def __init__(self):
        """Инициализирует диспетчер команд."""
        self._commands: Dict[str, Type[Command]] = {}
        self._middleware: list[Middleware] = []
    
    def register(self, command_class: Type[Command]) -> Type[Command]:
        """
        Регистрирует класс команды.
        
        Args:
            command_class: Класс команды для регистрации
            
        Returns:
            Type[Command]: Зарегистрированный класс команды
            
        Raises:
            ValueError: Если команда с таким именем уже зарегистрирована
        """
        if not command_class.name:
            raise ValueError("Command must have a name")
            
        if command_class.name in self._commands:
            raise ValueError(f"Command '{command_class.name}' is already registered")
            
        self._commands[command_class.name] = command_class
        logger.debug(f"Registered command: {command_class.name}")
        return command_class
    
    def command(self, name: str, description: str = "") -> Callable[[Type[Command]], Type[Command]]:
        """
        Декоратор для регистрации класса команды.
        
        Args:
            name: Имя команды
            description: Описание команды
            
        Returns:
            Callable: Декоратор для класса команды
        """
        def decorator(cls: Type[Command]) -> Type[Command]:
            """Декоратор для класса команды."""
            cls.name = name
            cls.description = description or cls.__doc__ or ""
            return self.register(cls)
        return decorator
    
    def add_middleware(self, middleware: Middleware) -> None:
        """
        Добавляет промежуточное ПО (middleware) в цепочку обработки.
        
        Args:
            middleware: Функция промежуточного ПО
        """
        self._middleware.append(middleware)
        logger.debug(f"Added middleware: {middleware.__name__}")
    
    def middleware(self, func: Middleware) -> Middleware:
        """
        Декоратор для регистрации промежуточного ПО.
        
        Args:
            func: Функция промежуточного ПО
            
        Returns:
            Middleware: Зарегистрированная функция промежуточного ПО
        """
        self.add_middleware(func)
        return func
    
    async def dispatch(self, command_name: str, params: Dict[str, Any], 
                       context: Optional[Context] = None) -> CommandResponse:
        """
        Выполняет команду с указанными параметрами.
        
        Args:
            command_name: Имя команды
            params: Параметры команды
            context: Контекст выполнения (опционально)
            
        Returns:
            CommandResponse: Результат выполнения команды
            
        Raises:
            CommandError: Если команда не найдена или произошла ошибка при выполнении
        """
        if command_name not in self._commands:
            raise CommandError(f"Unknown command: {command_name}")
        
        context = context or {}
        command_class = self._commands[command_name]
        command = command_class.create(context)
        
        try:
            # Выполняем цепочку middleware
            for middleware in self._middleware:
                await middleware(command, context)
            
            # Валидируем параметры
            await command.validate(params)
            
            # Выполняем команду
            logger.info(f"Executing command: {command_name}")
            result = await command.execute(params)
            
            if not isinstance(result, CommandResponse):
                result = CommandResponse(
                    success=True,
                    message="Command executed successfully",
                    data=result if isinstance(result, dict) else {"result": result}
                )
            
            return result
            
        except ValidationError as e:
            logger.warning(f"Validation error in command '{command_name}': {str(e)}")
            return CommandResponse(
                success=False,
                message=f"Validation error: {str(e)}",
                data={"error": "validation_error", "details": str(e)}
            )
        except CommandError as e:
            logger.error(f"Command error in '{command_name}': {str(e)}", exc_info=True)
            return CommandResponse(
                success=False,
                message=f"Command error: {str(e)}",
                data={"error": "command_error", "details": str(e)}
            )
        except Exception as e:
            logger.critical(f"Unexpected error in command '{command_name}': {str(e)}", exc_info=True)
            return CommandResponse(
                success=False,
                message="An unexpected error occurred",
                data={"error": "internal_error", "details": str(e)}
            )
    
    def get_commands_info(self) -> Dict[str, Dict[str, Any]]:
        """
        Возвращает информацию о всех зарегистрированных командах.
        
        Returns:
            Dict[str, Dict[str, Any]]: Словарь с информацией о командах
        """
        return {
            name: command_class.get_command_info()
            for name, command_class in self._commands.items()
        }
    
    def get_command_class(self, command_name: str) -> Optional[Type[Command]]:
        """
        Возвращает класс команды по имени.
        
        Args:
            command_name: Имя команды
            
        Returns:
            Optional[Type[Command]]: Класс команды или None, если команда не найдена
        """
        return self._commands.get(command_name)
