import os
import subprocess
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from config import settings
from core.utils import safe_execute_command
import logging
from pathlib import Path
import asyncio
import shlex
import sys
from typing import Dict, List, Optional, Tuple, Union, Any

logger = logging.getLogger(__name__)

class ExecutionResult:
    """Result of a command or script execution."""
    def __init__(self, success: bool, output: str, error: str, return_code: int, execution_time: float):
        self.success = success
        self.output = output
        self.error = error
        self.return_code = return_code
        self.execution_time = execution_time

class ScriptExecutor:
    """Handles script execution with safety checks and timeouts."""
    
    def __init__(self, project_root: Union[str, Path]):
        """Initialize with project root directory."""
        self.project_root = Path(project_root).resolve()
        self.allowed_commands = [
            'python', 'python3', 'pip', 'pip3', 'git',
            'ls', 'pwd', 'cat', 'grep', 'find', 'echo'
        ]
        self.max_execution_time = 300  # 5 minutes
    
    async def execute_script(
        self,
        script_path: Union[str, Path],
        args: Optional[List[str]] = None,
        timeout: Optional[int] = None
    ) -> ExecutionResult:
        """Execute a Python script with the given arguments."""
        script_path = self._validate_path(script_path)
        if not script_path:
            return ExecutionResult(
                success=False,
                output="",
                error="Script path is outside project directory or doesn't exist",
                return_code=1,
                execution_time=0.0
            )
        
        if not script_path.exists():
            return ExecutionResult(
                success=False,
                output="",
                error=f"Script not found: {script_path}",
                return_code=1,
                execution_time=0.0
            )
        
        cmd = [sys.executable, str(script_path)]
        if args:
            cmd.extend(args)
        
        return await self._run_command(cmd, cwd=script_path.parent, timeout=timeout)
    
    async def execute_command(
        self,
        command: str,
        cwd: Optional[Union[str, Path]] = None,
        timeout: Optional[int] = None
    ) -> ExecutionResult:
        """Execute a shell command with safety checks."""
        try:
            parts = shlex.split(command)
            if not parts:
                return ExecutionResult(
                    success=False,
                    output="",
                    error="Empty command",
                    return_code=1,
                    execution_time=0.0
                )
            
            # Check if command is allowed
            if parts[0] not in self.allowed_commands:
                return ExecutionResult(
                    success=False,
                    output="",
                    error=f"Command not allowed: {parts[0]}",
                    return_code=1,
                    execution_time=0.0
                )
            
            # Resolve working directory
            if cwd:
                cwd = Path(cwd).resolve()
                if not self._is_within_project(cwd):
                    return ExecutionResult(
                        success=False,
                        output="",
                        error="Working directory is outside project",
                        return_code=1,
                        execution_time=0.0
                    )
            else:
                cwd = self.project_root
            
            return await self._run_command(parts, cwd=cwd, timeout=timeout)
        
        except Exception as e:
            return ExecutionResult(
                success=False,
                output="",
                error=f"Command execution failed: {str(e)}",
                return_code=1,
                execution_time=0.0
            )
    
    async def _run_command(
        self,
        cmd: List[str],
        cwd: Path,
        timeout: Optional[int] = None
    ) -> ExecutionResult:
        """Run a command with timeout and capture output."""
        if timeout is None:
            timeout = self.max_execution_time
        
        start_time = asyncio.get_event_loop().time()
        process = None
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=str(cwd),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                limit=1024 * 1024,  # 1MB buffer
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout
                )
                
                execution_time = asyncio.get_event_loop().time() - start_time
                
                return ExecutionResult(
                    success=process.returncode == 0,
                    output=stdout.decode('utf-8', errors='replace') if stdout else "",
                    error=stderr.decode('utf-8', errors='replace') if stderr else "",
                    return_code=process.returncode if process.returncode is not None else -1,
                    execution_time=execution_time
                )
                
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return ExecutionResult(
                    success=False,
                    output="",
                    error=f"Command timed out after {timeout} seconds",
                    return_code=-1,
                    execution_time=timeout
                )
                
        except Exception as e:
            if process and process.returncode is None:
                process.kill()
                await process.wait()
                
            return ExecutionResult(
                success=False,
                output="",
                error=f"Command execution failed: {str(e)}",
                return_code=1,
                execution_time=asyncio.get_event_loop().time() - start_time
            )
        finally:
            if process and process.returncode is None:
                process.kill()
    
    def _validate_path(self, path: Union[str, Path]) -> Optional[Path]:
        """Validate that the path is within the project directory."""
        try:
            resolved = Path(path).resolve()
            if self._is_within_project(resolved):
                return resolved
            return None
        except Exception:
            return None
    
    def _is_within_project(self, path: Path) -> bool:
        """Check if a path is within the project directory."""
        try:
            path = path.resolve()
            return path.is_relative_to(self.project_root)
        except ValueError:
            return False

async def run_script(file_path: str, chat_id: int, context):
    """Запускает Python-скрипт с подтверждением"""
    executor = ScriptExecutor(os.getcwd())
    result = await executor.execute_script(file_path)
    
    if not result.success:
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"❌ Ошибка: {result.error}"
        )
        return
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Запустить", callback_data=f"run_script:{file_path}")],
        [InlineKeyboardButton("❌ Отмена", callback_data="cancel")]
    ])

    await context.bot.send_message(
        chat_id=chat_id,
        text=f"Запустить скрипт?\n`{file_path}`",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

async def run_cmd(command: str, chat_id: int, context):
    """Выполняет shell-команду с подтверждением"""
    executor = ScriptExecutor(os.getcwd())
    result = await executor.execute_command(command)
    
    if not result.success:
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"❌ Ошибка: {result.error}"
        )
        return
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Выполнить", callback_data=f"run_cmd:{command}")],
        [InlineKeyboardButton("❌ Отмена", callback_data="cancel")]
    ])

    await context.bot.send_message(
        chat_id=chat_id,
        text=f"Выполнить команду?\n`{command}`",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

async def install_dependencies(requirements_file: str = "requirements.txt"):
    """Устанавливает зависимости из файла"""
    if os.path.exists(requirements_file):
        result = safe_execute_command(f"pip install -r {requirements_file}")
        if not result["success"]:
            logger.error(f"Ошибка установки зависимостей: {result['error']}")