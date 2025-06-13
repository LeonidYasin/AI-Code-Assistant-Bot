"""
Команды для выполнения кода.

Этот модуль содержит команды для выполнения кода на различных языках
программирования с поддержкой изоляции и ограничений.
"""
import logging
import asyncio
import tempfile
import os
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field

from ..base import Command, CommandResponse, Context
from .base import ProjectCommand, ProjectCommandParams

logger = logging.getLogger(__name__)

@dataclass
class ExecuteCodeParams(ProjectCommandParams):
    """Параметры команды выполнения кода."""
    code: str
    language: str = "python"
    timeout: int = 30
    input_data: Optional[str] = None
    args: List[str] = field(default_factory=list)
    env: Dict[str, str] = field(default_factory=dict)

class ExecuteCodeCommand(ProjectCommand[ExecuteCodeParams]):
    """
    Команда для выполнения кода на различных языках программирования.
    
    Поддерживает выполнение кода с изоляцией и ограничениями,
    а также обработку ввода-вывода.
    """
    
    name = "execute_code"
    description = "Выполняет код на указанном языке программирования"
    
    # Поддерживаемые языки и их расширения файлов
    SUPPORTED_LANGUAGES = {
        'python': '.py',
        'python3': '.py',
        'bash': '.sh',
        'shell': '.sh',
        'javascript': '.js',
        'node': '.js',
        'ruby': '.rb',
        'perl': '.pl',
        'php': '.php',
        'lua': '.lua',
    }
    
    # Команды для запуска кода на разных языках
    RUN_COMMANDS = {
        'python': ['python3', '{file}'],
        'python3': ['python3', '{file}'],
        'bash': ['bash', '{file}'],
        'shell': ['sh', '{file}'],
        'javascript': ['node', '{file}'],
        'node': ['node', '{file}'],
        'ruby': ['ruby', '{file}'],
        'perl': ['perl', '{file}'],
        'php': ['php', '{file}'],
        'lua': ['lua', '{file}'],
    }
    
    async def execute(self, params: ExecuteCodeParams) -> CommandResponse:
        """
        Выполняет код на указанном языке программирования.
        
        Args:
            params: Параметры команды
            
        Returns:
            CommandResponse: Результат выполнения кода
        """
        try:
            # Проверяем поддержку языка
            language = params.language.lower()
            if language not in self.SUPPORTED_LANGUAGES:
                return CommandResponse(
                    success=False,
                    message=f"Unsupported language: {language}",
                    data={
                        'error': 'unsupported_language',
                        'supported_languages': list(self.SUPPORTED_LANGUAGES.keys())
                    }
                )
            
            # Создаем временную директорию для выполнения кода
            with tempfile.TemporaryDirectory(prefix='code_exec_') as temp_dir:
                temp_dir_path = Path(temp_dir)
                
                # Создаем файл с кодом
                ext = self.SUPPORTED_LANGUAGES[language]
                file_path = temp_dir_path / f"code{ext}"
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(params.code)
                
                # Делаем файл исполняемым, если это скрипт
                if language in ['bash', 'shell']:
                    os.chmod(file_path, 0o755)
                
                # Подготавливаем команду для выполнения
                cmd = self._prepare_command(language, file_path, params)
                
                # Запускаем выполнение кода
                result = await self._run_command(
                    cmd=cmd,
                    cwd=temp_dir_path,
                    input_data=params.input_data,
                    timeout=params.timeout,
                    env=params.env
                )
                
                return CommandResponse(
                    success=result['success'],
                    message=result['message'],
                    data={
                        'exit_code': result['exit_code'],
                        'stdout': result['stdout'],
                        'stderr': result['stderr'],
                        'execution_time': result['execution_time'],
                        'timed_out': result['timed_out'],
                        'language': language
                    }
                )
                
        except Exception as e:
            logger.error(f"Failed to execute code: {str(e)}", exc_info=True)
            return CommandResponse(
                success=False,
                message=f"Failed to execute code: {str(e)}",
                data={
                    'error': 'execution_failed',
                    'details': str(e)
                }
            )
    
    def _prepare_command(
        self,
        language: str,
        file_path: Path,
        params: ExecuteCodeParams
    ) -> List[str]:
        """
        Подготавливает команду для выполнения кода.
        
        Args:
            language: Язык программирования
            file_path: Путь к файлу с кодом
            params: Параметры команды
            
        Returns:
            List[str]: Команда для выполнения
        """
        # Получаем базовую команду для языка
        cmd_template = self.RUN_COMMANDS[language]
        
        # Заменяем плейсхолдеры в команде
        cmd = []
        for part in cmd_template:
            cmd.append(part.format(file=str(file_path)))
        
        # Добавляем аргументы командной строки
        if params.args:
            cmd.extend(params.args)
        
        return cmd
    
    async def _run_command(
        self,
        cmd: List[str],
        cwd: Path,
        input_data: Optional[str] = None,
        timeout: int = 30,
        env: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Запускает команду с указанными параметрами.
        
        Args:
            cmd: Команда для выполнения
            cwd: Рабочая директория
            input_data: Входные данные для команды
            timeout: Таймаут выполнения в секундах
            env: Переменные окружения
            
        Returns:
            Dict[str, Any]: Результат выполнения команды
        """
        # Подготавливаем переменные окружения
        process_env = os.environ.copy()
        if env:
            process_env.update(env)
        
        # Запускаем процесс
        process = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=cwd,
            stdin=asyncio.subprocess.PIPE if input_data else asyncio.subprocess.DEVNULL,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=process_env
        )
        
        # Отправляем входные данные, если они есть
        stdin_data = input_data.encode('utf-8') if input_data else None
        
        # Засекаем время выполнения
        start_time = asyncio.get_event_loop().time()
        
        try:
            # Ожидаем завершения процесса с таймаутом
            stdout_data, stderr_data = await asyncio.wait_for(
                process.communicate(stdin_data),
                timeout=timeout
            )
            timed_out = False
        except asyncio.TimeoutError:
            # Прерываем процесс по таймауту
            process.terminate()
            try:
                await asyncio.wait_for(process.wait(), timeout=1)
            except (asyncio.TimeoutError, ProcessLookupError):
                process.kill()
                await process.wait()
            
            stdout_data = b""
            stderr_data = f"Command timed out after {timeout} seconds".encode('utf-8')
            timed_out = True
        
        # Вычисляем время выполнения
        execution_time = asyncio.get_event_loop().time() - start_time
        
        # Декодируем вывод
        stdout = stdout_data.decode('utf-8', errors='replace').strip()
        stderr = stderr_data.decode('utf-8', errors='replace').strip()
        
        # Определяем статус выполнения
        success = process.returncode == 0 and not timed_out
        
        return {
            'success': success,
            'message': 'Code executed successfully' if success else 'Code execution failed',
            'exit_code': process.returncode,
            'stdout': stdout,
            'stderr': stderr,
            'execution_time': execution_time,
            'timed_out': timed_out,
            'command': ' '.join(cmd)
        }

@dataclass
class ExecuteFileParams(ProjectCommandParams):
    """Параметры команды выполнения файла."""
    file_path: str
    language: Optional[str] = None
    args: List[str] = field(default_factory=list)
    env: Dict[str, str] = field(default_factory=dict)
    timeout: int = 30
    input_data: Optional[str] = None

class ExecuteFileCommand(ProjectCommand[ExecuteFileParams]):
    """
    Команда для выполнения файла с кодом.
    
    Поддерживает выполнение файлов с кодом на различных языках
    программирования с автоматическим определением языка.
    """
    
    name = "execute_file"
    description = "Выполняет файл с кодом на указанном языке программирования"
    
    async def execute(self, params: ExecuteFileParams) -> CommandResponse:
        """
        Выполняет файл с кодом.
        
        Args:
            params: Параметры команды
            
        Returns:
            CommandResponse: Результат выполнения файла
        """
        try:
            # Получаем полный путь к файлу
            file_path = Path(params.file_path)
            if not file_path.is_absolute():
                project_id = self.get_project_id(params)
                if project_id:
                    project = await self.project_manager.get_project(project_id)
                    file_path = project.path / file_path
            
            # Проверяем существование файла
            if not file_path.exists() or not file_path.is_file():
                return CommandResponse(
                    success=False,
                    message=f"File not found: {file_path}",
                    data={'error': 'file_not_found'}
                )
            
            # Определяем язык, если не указан
            language = params.language
            if not language:
                language = self._detect_language(file_path)
            
            # Читаем содержимое файла
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                code = f.read()
            
            # Используем команду выполнения кода
            execute_code_cmd = ExecuteCodeCommand(self.context)
            return await execute_code_cmd.execute(ExecuteCodeParams(
                code=code,
                language=language,
                timeout=params.timeout,
                input_data=params.input_data,
                args=params.args,
                env=params.env
            ))
            
        except Exception as e:
            logger.error(f"Failed to execute file: {str(e)}", exc_info=True)
            return CommandResponse(
                success=False,
                message=f"Failed to execute file: {str(e)}",
                data={
                    'error': 'file_execution_failed',
                    'details': str(e)
                }
            )
    
    def _detect_language(self, file_path: Path) -> str:
        """
        Определяет язык программирования по расширению файла.
        
        Args:
            file_path: Путь к файлу
            
        Returns:
            str: Идентификатор языка программирования
        """
        # Сопоставление расширений с языками
        extension_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.rb': 'ruby',
            '.pl': 'perl',
            '.php': 'php',
            '.lua': 'lua',
            '.sh': 'bash'
        }
        
        # Пытаемся определить язык по расширению
        ext = file_path.suffix.lower()
        if ext in extension_map:
            return extension_map[ext]
        
        # Если расширение неизвестно, пытаемся определить по шебангу
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                first_line = f.readline().strip()
                
            if first_line.startswith('#!'):
                shebang = first_line[2:].strip()
                if 'python' in shebang:
                    return 'python'
                elif 'node' in shebang:
                    return 'javascript'
                elif 'ruby' in shebang:
                    return 'ruby'
                elif 'perl' in shebang:
                    return 'perl'
                elif 'php' in shebang:
                    return 'php'
                elif 'lua' in shebang:
                    return 'lua'
                elif 'bash' in shebang or 'sh' in shebang:
                    return 'bash'
        except Exception:
            pass
        
        # По умолчанию считаем, что это текстовый файл
        return 'text'
