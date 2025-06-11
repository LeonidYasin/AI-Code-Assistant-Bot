"""Handlers for code analysis and execution."""
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters
from typing import Dict, Any, Optional, List, Tuple
import logging

from handlers.base import BaseHandler
from core.project.manager import ProjectManager

logger = logging.getLogger(__name__)

class CodeHandler(BaseHandler):
    """Handler for code analysis and execution."""
    
    def __init__(self, project_manager: ProjectManager):
        super().__init__()
        self.project_manager = project_manager
    
    def get_commands(self) -> Dict[str, dict]:
        """Return supported commands and their handlers."""
        return {
            'analyze': {
                'description': 'Проанализировать код',
                'handler': self.handle_analyze_code,
                'help': (
                    "Использование: /analyze <код>\n"
                    "Анализирует предоставленный код."
                )
            },
            'analyze_file': {
                'description': 'Проанализировать файл с кодом',
                'handler': self.handle_analyze_file,
                'help': (
                    "Использование: /analyze_file <путь_к_файлу>\n"
                    "Анализирует код в указанном файле."
                )
            },
            'analyze_project': {
                'description': 'Проанализировать весь проект',
                'handler': self.handle_analyze_project,
                'help': (
                    "Использование: /analyze_project\n"
                    "Анализирует весь текущий проект."
                )
            },
            'run': {
                'description': 'Запустить скрипт',
                'handler': self.handle_run_script,
                'help': (
                    "Использование: /run <путь_к_файлу> [аргументы]\n"
                    "Запускает указанный скрипт."
                )
            },
            'cmd': {
                'description': 'Выполнить команду в оболочке',
                'handler': self.handle_shell_command,
                'help': (
                    "Использование: /cmd <команда>\n"
                    "Выполняет команду в оболочке."
                )
            }
        }
    
    async def handle_analyze_code(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> Optional[str]:
        """Handle analyze code command."""
        if not self._check_project_selected(update):
            return None
            
        if not context.args:
            return "❌ Укажите код для анализа: /analyze <код>"
            
        code = ' '.join(context.args)
        success, result = self.project_manager.analyze_code(code, is_content=True)
        
        if not success:
            return f"❌ Ошибка: {result}"
            
        return f"🔍 Анализ кода:\n\n{result}"
    
    async def handle_analyze_file(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> Optional[str]:
        """Handle analyze file command."""
        if not self._check_project_selected(update):
            return None
            
        if not context.args:
            return "❌ Укажите путь к файлу: /analyze_file <путь_к_файлу>"
            
        file_path = ' '.join(context.args)
        success, result = self.project_manager.analyze_code(file_path)
        
        if not success:
            return f"❌ Ошибка: {result}"
            
        return f"🔍 Анализ файла {file_path}:\n\n{result}"
    
    async def handle_analyze_project(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> Optional[str]:
        """Handle analyze project command."""
        if not self._check_project_selected(update):
            return None
            
        success, result = self.project_manager.analyze_project()
        
        if not success:
            return f"❌ Ошибка: {result}"
            
        return f"🔍 Анализ проекта:\n\n{result}"
    
    async def handle_run_script(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> Optional[str]:
        """Handle run script command."""
        if not self._check_project_selected(update):
            return None
            
        if not context.args:
            return "❌ Укажите путь к скрипту: /run <путь_к_скрипту> [аргументы]"
            
        script_path = context.args[0]
        args = context.args[1:] if len(context.args) > 1 else []
        
        success, result = self.project_manager.run_script(script_path, args)
        
        if not success:
            return f"❌ Ошибка: {result}"
            
        return f"🚀 Результат выполнения {script_path}:\n\n{result}"
    
    async def handle_shell_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> Optional[str]:
        """Handle shell command execution."""
        if not self._check_project_selected(update):
            return None
            
        if not context.args:
            return "❌ Укажите команду: /cmd <команда>"
            
        command = ' '.join(context.args)
        success, result = self.project_manager.execute_command(command)
        
        if not success:
            return f"❌ Ошибка: {result}"
            
        return f"💻 Результат команды '{command}':\n\n{result}"
    
    def _check_project_selected(self, update: Update) -> bool:
        """Check if a project is selected."""
        if not self.project_manager.current_project:
            update.message.reply_text(
                "ℹ️ Сначала выберите проект: /project switch <имя_проекта>"
            )
            return False
        return True
