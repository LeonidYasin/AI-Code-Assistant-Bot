"""
Команды для управления зависимостями проекта.

Этот модуль содержит команды для управления зависимостями проекта,
такие как установка, обновление и удаление пакетов.
"""
import logging
import subprocess
import sys
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field

from ..base import Command, CommandResponse, Context
from .base import ProjectCommand, ProjectCommandParams

logger = logging.getLogger(__name__)

@dataclass
class InstallDependenciesParams(ProjectCommandParams):
    """Параметры команды установки зависимостей."""
    packages: List[str] = field(default_factory=list)
    dev: bool = False
    file: Optional[str] = None
    no_cache: bool = False
    upgrade: bool = False
    no_deps: bool = False

class InstallDependenciesCommand(ProjectCommand[InstallDependenciesParams]):
    """
    Команда для установки зависимостей проекта.
    
    Поддерживает установку пакетов из различных источников,
    включая PyPI, Git-репозитории и локальные пакеты.
    """
    
    name = "install_dependencies"
    description = "Устанавливает зависимости проекта"
    
    async def execute(self, params: InstallDependenciesParams) -> CommandResponse:
        """
        Выполняет установку зависимостей.
        
        Args:
            params: Параметры команды
            
        Returns:
            CommandResponse: Результат установки зависимостей
        """
        try:
            project_id = self.get_project_id(params)
            project = await self.project_manager.get_project(project_id) if project_id else None
            
            # Определяем рабочую директорию
            cwd = project.path if project else Path.cwd()
            
            # Проверяем наличие файла requirements.txt
            requirements_file = Path(params.file) if params.file else cwd / 'requirements.txt'
            if not requirements_file.is_absolute():
                requirements_file = cwd / requirements_file
            
            # Подготавливаем команду pip
            pip_cmd = self._prepare_pip_command(
                action='install',
                packages=params.packages,
                dev=params.dev,
                requirements_file=requirements_file if not params.packages and requirements_file.exists() else None,
                no_cache=params.no_cache,
                upgrade=params.upgrade,
                no_deps=params.no_deps
            )
            
            # Запускаем установку
            result = await self._run_pip_command(pip_cmd, cwd)
            
            if result['success']:
                return CommandResponse(
                    success=True,
                    message="Dependencies installed successfully",
                    data={
                        'installed': params.packages or f"from {requirements_file}",
                        'output': result['output']
                    }
                )
            else:
                return CommandResponse(
                    success=False,
                    message="Failed to install dependencies",
                    data={
                        'error': 'installation_failed',
                        'details': result['error'],
                        'output': result['output']
                    }
                )
                
        except Exception as e:
            logger.error(f"Failed to install dependencies: {str(e)}", exc_info=True)
            return CommandResponse(
                success=False,
                message=f"Failed to install dependencies: {str(e)}",
                data={
                    'error': 'installation_failed',
                    'details': str(e)
                }
            )
    
    def _prepare_pip_command(
        self,
        action: str,
        packages: List[str] = None,
        dev: bool = False,
        requirements_file: Path = None,
        no_cache: bool = False,
        upgrade: bool = False,
        no_deps: bool = False
    ) -> List[str]:
        """
        Подготавливает команду pip для выполнения.
        
        Args:
            action: Действие (install, uninstall, freeze и т.д.)
            packages: Список пакетов
            dev: Установка в раздел разработки
            requirements_file: Файл с зависимостями
            no_cache: Не использовать кеш
            upgrade: Обновить пакеты до последних версий
            no_deps: Не устанавливать зависимости
            
        Returns:
            List[str]: Команда для выполнения
        """
        cmd = [sys.executable, '-m', 'pip', '--disable-pip-version-check']
        
        if action == 'install':
            cmd.append('install')
            
            if upgrade:
                cmd.append('--upgrade')
            
            if no_cache:
                cmd.append('--no-cache-dir')
            
            if no_deps:
                cmd.append('--no-deps')
            
            if dev:
                # Устанавливаем в режиме разработки (editable)
                cmd.append('-e')
            
            if requirements_file:
                cmd.append('-r')
                cmd.append(str(requirements_file))
            elif packages:
                cmd.extend(packages)
        
        elif action == 'uninstall':
            cmd.extend(['uninstall', '-y'])
            if packages:
                cmd.extend(packages)
        
        elif action == 'freeze':
            cmd.append('freeze')
        
        elif action == 'list':
            cmd.append('list')
        
        return cmd
    
    async def _run_pip_command(self, cmd: List[str], cwd: Path) -> Dict[str, Any]:
        """
        Запускает команду pip и возвращает результат.
        
        Args:
            cmd: Команда для выполнения
            cwd: Рабочая директория
            
        Returns:
            Dict[str, Any]: Результат выполнения команды
        """
        try:
            logger.info(f"Running command: {' '.join(cmd)}")
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=cwd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            output = stdout.decode('utf-8', errors='replace').strip()
            error = stderr.decode('utf-8', errors='replace').strip()
            
            return {
                'success': process.returncode == 0,
                'output': output,
                'error': error if process.returncode != 0 else None,
                'returncode': process.returncode
            }
            
        except Exception as e:
            logger.error(f"Error running pip command: {str(e)}", exc_info=True)
            return {
                'success': False,
                'output': '',
                'error': str(e),
                'returncode': 1
            }

@dataclass
class UninstallDependenciesParams(ProjectCommandParams):
    """Параметры команды удаления зависимостей."""
    packages: List[str] = field(default_factory=list)
    file: Optional[str] = None

class UninstallDependenciesCommand(ProjectCommand[UninstallDependenciesParams]):
    """
    Команда для удаления зависимостей проекта.
    
    Поддерживает удаление пакетов по именам или из файла requirements.
    """
    
    name = "uninstall_dependencies"
    description = "Удаляет зависимости проекта"
    
    async def execute(self, params: UninstallDependenciesParams) -> CommandResponse:
        """
        Выполняет удаление зависимостей.
        
        Args:
            params: Параметры команды
            
        Returns:
            CommandResponse: Результат удаления зависимостей
        """
        try:
            project_id = self.get_project_id(params)
            project = await self.project_manager.get_project(project_id) if project_id else None
            
            # Определяем рабочую директорию
            cwd = project.path if project else Path.cwd()
            
            # Проверяем наличие файла requirements.txt, если указан
            packages = params.packages.copy()
            if params.file:
                requirements_file = Path(params.file)
                if not requirements_file.is_absolute():
                    requirements_file = cwd / requirements_file
                
                if requirements_file.exists():
                    with open(requirements_file, 'r', encoding='utf-8') as f:
                        # Читаем пакеты из файла, пропуская пустые строки и комментарии
                        req_packages = [
                            line.split('#')[0].strip()
                            for line in f.readlines()
                            if line.strip() and not line.strip().startswith('#')
                        ]
                        packages.extend(req_packages)
            
            if not packages:
                return CommandResponse(
                    success=False,
                    message="No packages specified for uninstallation",
                    data={'error': 'no_packages_specified'}
                )
            
            # Подготавливаем команду pip
            pip_cmd = self._prepare_pip_command('uninstall', packages=packages)
            
            # Запускаем удаление
            result = await self._run_pip_command(pip_cmd, cwd)
            
            if result['success']:
                return CommandResponse(
                    success=True,
                    message="Dependencies uninstalled successfully",
                    data={
                        'uninstalled': packages,
                        'output': result['output']
                    }
                )
            else:
                return CommandResponse(
                    success=False,
                    message="Failed to uninstall dependencies",
                    data={
                        'error': 'uninstallation_failed',
                        'details': result['error'],
                        'output': result['output']
                    }
                )
                
        except Exception as e:
            logger.error(f"Failed to uninstall dependencies: {str(e)}", exc_info=True)
            return CommandResponse(
                success=False,
                message=f"Failed to uninstall dependencies: {str(e)}",
                data={
                    'error': 'uninstallation_failed',
                    'details': str(e)
                }
            )

@dataclass
class ListDependenciesParams(ProjectCommandParams):
    """Параметры команды вывода списка зависимостей."""
    format: str = 'list'  # 'list' или 'json'
    outdated: bool = False

class ListDependenciesCommand(ProjectCommand[ListDependenciesParams]):
    """
    Команда для вывода списка зависимостей проекта.
    
    Поддерживает различные форматы вывода и проверку обновлений.
    """
    
    name = "list_dependencies"
    description = "Выводит список зависимостей проекта"
    
    async def execute(self, params: ListDependenciesParams) -> CommandResponse:
        """
        Выводит список зависимостей.
        
        Args:
            params: Параметры команды
            
        Returns:
            CommandResponse: Список зависимостей
        """
        try:
            project_id = self.get_project_id(params)
            project = await self.project_manager.get_project(project_id) if project_id else None
            
            # Определяем рабочую директорию
            cwd = project.path if project else Path.cwd()
            
            # Подготавливаем команду pip
            pip_cmd = self._prepare_pip_command('list')
            if params.outdated:
                pip_cmd.append('--outdated')
            
            # Запускаем команду
            result = await self._run_pip_command(pip_cmd, cwd)
            
            if not result['success']:
                return CommandResponse(
                    success=False,
                    message="Failed to list dependencies",
                    data={
                        'error': 'list_failed',
                        'details': result['error'],
                        'output': result['output']
                    }
                )
            
            # Обрабатываем вывод в зависимости от формата
            if params.format.lower() == 'json':
                # Преобразуем вывод в JSON
                dependencies = self._parse_pip_list_output(result['output'])
                output = json.dumps(dependencies, indent=2, ensure_ascii=False)
            else:
                # Оставляем вывод как есть
                output = result['output']
                dependencies = self._parse_pip_list_output(output)
            
            return CommandResponse(
                success=True,
                message=f"Found {len(dependencies)} dependencies",
                data={
                    'dependencies': dependencies,
                    'output': output,
                    'count': len(dependencies)
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to list dependencies: {str(e)}", exc_info=True)
            return CommandResponse(
                success=False,
                message=f"Failed to list dependencies: {str(e)}",
                data={
                    'error': 'list_failed',
                    'details': str(e)
                }
            )
    
    def _parse_pip_list_output(self, output: str) -> List[Dict[str, str]]:
        """
        Разбирает вывод команды pip list в список словарей.
        
        Args:
            output: Вывод команды pip list
            
        Returns:
            List[Dict[str, str]]: Список зависимостей
        """
        lines = output.strip().split('\n')
        if not lines:
            return []
        
        # Пропускаем заголовок
        header = lines[0].lower()
        if 'package' in header and 'version' in header:
            lines = lines[2:]  # Пропускаем заголовок и разделитель
        
        dependencies = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Разбиваем строку на колонки
            parts = line.split()
            if not parts:
                continue
                
            package = parts[0]
            version = parts[1] if len(parts) > 1 else None
            latest = parts[2] if len(parts) > 2 and parts[2].startswith('(') and parts[2].endswith(')') else None
            
            if latest:
                latest = latest.strip('()')
            
            dependencies.append({
                'package': package,
                'version': version,
                'latest': latest if latest and latest != version else None
            })
        
        return dependencies
