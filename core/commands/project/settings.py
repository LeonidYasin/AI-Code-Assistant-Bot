"""
Команды для управления настройками проекта.

Этот модуль содержит команды для работы с настройками проекта,
такие как получение, установка и удаление параметров конфигурации.
"""
import logging
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, TypeVar, Generic, Type, cast
from dataclasses import dataclass, field, asdict

from ..base import Command, CommandResponse, Context
from .base import ProjectCommand, ProjectCommandParams

logger = logging.getLogger(__name__)

# Тип для значений настроек
SettingValue = Union[str, int, float, bool, List[Any], Dict[str, Any], None]

@dataclass
class GetSettingParams(ProjectCommandParams):
    """Параметры команды получения настройки."""
    key: str
    default: Optional[SettingValue] = None

class GetSettingCommand(ProjectCommand[GetSettingParams]):
    """
    Команда для получения значения настройки проекта.
    
    Возвращает значение настройки по указанному ключу или значение по умолчанию,
    если настройка не найдена.
    """
    
    name = "get_setting"
    description = "Возвращает значение настройки проекта"
    
    async def execute(self, params: GetSettingParams) -> CommandResponse:
        """
        Получает значение настройки.
        
        Args:
            params: Параметры команды
            
        Returns:
            CommandResponse: Значение настройки
        """
        try:
            project_id = self.get_project_id(params)
            project = await self.project_manager.get_project(project_id) if project_id else None
            
            if not project:
                return CommandResponse(
                    success=False,
                    message="Project not found",
                    data={'error': 'project_not_found'}
                )
            
            # Получаем значение настройки
            value = project.settings.get(params.key, params.default)
            
            return CommandResponse(
                success=True,
                message=f"Setting '{params.key}' retrieved successfully",
                data={
                    'key': params.key,
                    'value': value,
                    'is_default': params.key not in project.settings
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to get setting: {str(e)}", exc_info=True)
            return CommandResponse(
                success=False,
                message=f"Failed to get setting: {str(e)}",
                data={
                    'error': 'get_setting_failed',
                    'details': str(e)
                }
            )

@dataclass
class SetSettingParams(ProjectCommandParams):
    """Параметры команды установки настройки."""
    key: str
    value: SettingValue

class SetSettingCommand(ProjectCommand[SetSettingParams]):
    """
    Команда для установки значения настройки проекта.
    
    Устанавливает значение настройки по указанному ключу.
    Если настройка уже существует, её значение будет перезаписано.
    """
    
    name = "set_setting"
    description = "Устанавливает значение настройки проекта"
    
    async def execute(self, params: SetSettingParams) -> CommandResponse:
        """
        Устанавливает значение настройки.
        
        Args:
            params: Параметры команды
            
        Returns:
            CommandResponse: Результат установки настройки
        """
        try:
            project_id = self.get_project_id(params)
            project = await self.project_manager.get_project(project_id) if project_id else None
            
            if not project:
                return CommandResponse(
                    success=False,
                    message="Project not found",
                    data={'error': 'project_not_found'}
                )
            
            # Получаем предыдущее значение настройки
            old_value = project.settings.get(params.key)
            
            # Устанавливаем новое значение
            project.settings[params.key] = params.value
            
            # Сохраняем изменения
            await project.save()
            
            return CommandResponse(
                success=True,
                message=f"Setting '{params.key}' set successfully",
                data={
                    'key': params.key,
                    'old_value': old_value,
                    'new_value': params.value
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to set setting: {str(e)}", exc_info=True)
            return CommandResponse(
                success=False,
                message=f"Failed to set setting: {str(e)}",
                data={
                    'error': 'set_setting_failed',
                    'details': str(e)
                }
            )

@dataclass
class DeleteSettingParams(ProjectCommandParams):
    """Параметры команды удаления настройки."""
    key: str

class DeleteSettingCommand(ProjectCommand[DeleteSettingParams]):
    """
    Команда для удаления настройки проекта.
    
    Удаляет настройку с указанным ключом из конфигурации проекта.
    """
    
    name = "delete_setting"
    description = "Удаляет настройку проекта"
    
    async def execute(self, params: DeleteSettingParams) -> CommandResponse:
        """
        Удаляет настройку.
        
        Args:
            params: Параметры команды
            
        Returns:
            CommandResponse: Результат удаления настройки
        """
        try:
            project_id = self.get_project_id(params)
            project = await self.project_manager.get_project(project_id) if project_id else None
            
            if not project:
                return CommandResponse(
                    success=False,
                    message="Project not found",
                    data={'error': 'project_not_found'}
                )
            
            # Проверяем существование настройки
            if params.key not in project.settings:
                return CommandResponse(
                    success=False,
                    message=f"Setting '{params.key}' not found",
                    data={'error': 'setting_not_found'}
                )
            
            # Получаем значение настройки перед удалением
            old_value = project.settings[params.key]
            
            # Удаляем настройку
            del project.settings[params.key]
            
            # Сохраняем изменения
            await project.save()
            
            return CommandResponse(
                success=True,
                message=f"Setting '{params.key}' deleted successfully",
                data={
                    'key': params.key,
                    'old_value': old_value
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to delete setting: {str(e)}", exc_info=True)
            return CommandResponse(
                success=False,
                message=f"Failed to delete setting: {str(e)}",
                data={
                    'error': 'delete_setting_failed',
                    'details': str(e)
                }
            )

@dataclass
class ListSettingsParams(ProjectCommandParams):
    """Параметры команды вывода списка настроек."""
    prefix: Optional[str] = None
    as_dict: bool = False

class ListSettingsCommand(ProjectCommand[ListSettingsParams]):
    """
    Команда для вывода списка всех настроек проекта.
    
    Возвращает список всех настроек проекта с их значениями.
    Поддерживает фильтрацию по префиксу ключа.
    """
    
    name = "list_settings"
    description = "Выводит список всех настроек проекта"
    
    async def execute(self, params: ListSettingsParams) -> CommandResponse:
        """
        Выводит список настроек.
        
        Args:
            params: Параметры команды
            
        Returns:
            CommandResponse: Список настроек
        """
        try:
            project_id = self.get_project_id(params)
            project = await self.project_manager.get_project(project_id) if project_id else None
            
            if not project:
                return CommandResponse(
                    success=False,
                    message="Project not found",
                    data={'error': 'project_not_found'}
                )
            
            # Фильтруем настройки по префиксу, если указан
            settings = {}
            for key, value in project.settings.items():
                if not params.prefix or key.startswith(params.prefix):
                    settings[key] = value
            
            # Формируем результат в зависимости от формата
            if params.as_dict:
                result = settings
            else:
                result = [
                    {'key': key, 'value': value}
                    for key, value in settings.items()
                ]
            
            return CommandResponse(
                success=True,
                message=f"Found {len(settings)} settings",
                data={
                    'settings': result,
                    'count': len(settings)
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to list settings: {str(e)}", exc_info=True)
            return CommandResponse(
                success=False,
                message=f"Failed to list settings: {str(e)}",
                data={
                    'error': 'list_settings_failed',
                    'details': str(e)
                }
            )

@dataclass
class ImportSettingsParams(ProjectCommandParams):
    """Параметры команды импорта настроек."""
    settings: Dict[str, Any]
    overwrite: bool = False
    merge: bool = True

class ImportSettingsCommand(ProjectCommand[ImportSettingsParams]):
    """
    Команда для импорта настроек проекта.
    
    Позволяет импортировать настройки из словаря.
    Поддерживает режимы перезаписи и слияния с существующими настройками.
    """
    
    name = "import_settings"
    description = "Импортирует настройки проекта из словаря"
    
    async def execute(self, params: ImportSettingsParams) -> CommandResponse:
        """
        Импортирует настройки.
        
        Args:
            params: Параметры команды
            
        Returns:
            CommandResponse: Результат импорта настроек
        """
        try:
            project_id = self.get_project_id(params)
            project = await self.project_manager.get_project(project_id) if project_id else None
            
            if not project:
                return CommandResponse(
                    success=False,
                    message="Project not found",
                    data={'error': 'project_not_found'}
                )
            
            # Создаем копию текущих настроек
            old_settings = project.settings.copy()
            
            # Применяем импортируемые настройки
            if params.overwrite:
                # Полная замена текущих настроек
                project.settings = params.settings.copy()
            elif params.merge:
                # Слияние с текущими настройками
                project.settings.update(params.settings)
            else:
                # Добавление только новых настроек
                for key, value in params.settings.items():
                    if key not in project.settings:
                        project.settings[key] = value
            
            # Сохраняем изменения
            await project.save()
            
            # Определяем добавленные и измененные настройки
            added = []
            updated = []
            
            for key, value in params.settings.items():
                if key not in old_settings:
                    added.append(key)
                elif old_settings[key] != value:
                    updated.append(key)
            
            return CommandResponse(
                success=True,
                message=f"Imported {len(params.settings)} settings ({len(added)} added, {len(updated)} updated)",
                data={
                    'added': added,
                    'updated': updated,
                    'total': len(project.settings)
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to import settings: {str(e)}", exc_info=True)
            return CommandResponse(
                success=False,
                message=f"Failed to import settings: {str(e)}",
                data={
                    'error': 'import_settings_failed',
                    'details': str(e)
                }
            )

@dataclass
class ExportSettingsParams(ProjectCommandParams):
    """Параметры команды экспорта настроек."""
    prefix: Optional[str] = None
    format: str = 'json'  # 'json' или 'dict'

class ExportSettingsCommand(ProjectCommand[ExportSettingsParams]):
    """
    Команда для экспорта настроек проекта.
    
    Возвращает настройки проекта в указанном формате.
    Поддерживает фильтрацию по префиксу ключа.
    """
    
    name = "export_settings"
    description = "Экспортирует настройки проекта в указанном формате"
    
    async def execute(self, params: ExportSettingsParams) -> CommandResponse:
        """
        Экспортирует настройки.
        
        Args:
            params: Параметры команды
            
        Returns:
            CommandResponse: Экспортированные настройки
        """
        try:
            project_id = self.get_project_id(params)
            project = await self.project_manager.get_project(project_id) if project_id else None
            
            if not project:
                return CommandResponse(
                    success=False,
                    message="Project not found",
                    data={'error': 'project_not_found'}
                )
            
            # Фильтруем настройки по префиксу, если указан
            settings = {}
            for key, value in project.settings.items():
                if not params.prefix or key.startswith(params.prefix):
                    settings[key] = value
            
            # Форматируем результат
            if params.format.lower() == 'json':
                result = json.dumps(settings, indent=2, ensure_ascii=False)
            else:
                result = settings
            
            return CommandResponse(
                success=True,
                message=f"Exported {len(settings)} settings",
                data={
                    'settings': result,
                    'count': len(settings),
                    'format': params.format
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to export settings: {str(e)}", exc_info=True)
            return CommandResponse(
                success=False,
                message=f"Failed to export settings: {str(e)}",
                data={
                    'error': 'export_settings_failed',
                    'details': str(e)
                }
            )
