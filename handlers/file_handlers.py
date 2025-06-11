"""Handlers for file operations."""
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters
from typing import Dict, Any, Optional, List, Tuple
import logging
import os
from pathlib import Path

from handlers.base import BaseHandler
from core.project.manager import ProjectManager

logger = logging.getLogger(__name__)

class FileHandler(BaseHandler):
    """Handler for file operations."""
    
    def __init__(self, project_manager: ProjectManager):
        super().__init__()
        self.project_manager = project_manager
    
    def get_commands(self) -> Dict[str, dict]:
        """Return supported commands and their handlers."""
        return {
            'list': {
                'description': 'Показать список файлов в проекте',
                'handler': self.handle_list_files,
                'help': (
                    "Использование: /list [путь]\n"
                    "Показывает список файлов и папок в текущем или указанном каталоге."
                )
            },
            'read': {
                'description': 'Показать содержимое файла',
                'handler': self.handle_read_file,
                'help': (
                    "Использование: /read <путь_к_файлу>\n"
                    "Показывает содержимое указанного файла."
                )
            },
            'create': {
                'description': 'Создать файл',
                'handler': self.handle_create_file,
                'help': (
                    "Использование: /create <путь_к_файлу> [содержимое]\n"
                    "Создает новый файл с указанным содержимым."
                )
            },
            'delete': {
                'description': 'Удалить файл',
                'handler': self.handle_delete_file,
                'help': (
                    "Использование: /delete <путь_к_файлу>\n"
                    "Удаляет указанный файл."
                )
            }
        }
    
    async def handle_list_files(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> Optional[str]:
        """Handle list files command."""
        if not self._check_project_selected(update):
            return None
            
        path = ' '.join(context.args) if context.args else '.'
        success, result = self.project_manager.list_files(path)
        
        if not success:
            return f"❌ Ошибка: {result}"
            
        if not result:
            return f"📂 Директория {path} пуста"
            
        files_list = ["📂 Содержимое директории:"]
        for item in result:
            item_type = "📁" if item['type'] == 'directory' else "📄"
            size = f" ({item['size']} bytes)" if item['type'] == 'file' else ""
            files_list.append(f"{item_type} {item['path']}{size}")
            
        return "\n".join(files_list)
    
    async def handle_read_file(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> Optional[str]:
        """Handle read file command."""
        if not self._check_project_selected(update):
            return None
            
        if not context.args:
            return "❌ Укажите путь к файлу: /read <путь_к_файлу>"
            
        file_path = ' '.join(context.args)
        success, content = self.project_manager.read_file(file_path)
        
        if not success:
            return f"❌ Ошибка: {content}"
            
        return f"📄 Содержимое файла {file_path}:\n\n```\n{content}\n```"
    
    async def handle_create_file(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> Optional[str]:
        """Handle create file command."""
        if not self._check_project_selected(update):
            return None
            
        if not context.args:
            return "❌ Укажите путь к файлу: /create <путь_к_файлу> [содержимое]"
            
        file_path = context.args[0]
        content = ' '.join(context.args[1:]) if len(context.args) > 1 else ''
        
        success, message = self.project_manager.create_file(file_path, content)
        if not success:
            return f"❌ Ошибка: {message}"
            
        return f"✅ Файл создан: {file_path}"
    
    async def handle_delete_file(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> Optional[str]:
        """Handle delete file command."""
        if not self._check_project_selected(update):
            return None
            
        if not context.args:
            return "❌ Укажите путь к файлу: /delete <путь_к_файлу>"
            
        file_path = ' '.join(context.args)
        success, message = self.project_manager.delete_file(file_path)
        
        if not success:
            return f"❌ Ошибка: {message}"
            
        return f"✅ Файл удален: {file_path}"
    
    def _check_project_selected(self, update: Update) -> bool:
        """Check if a project is selected."""
        if not self.project_manager.current_project:
            update.message.reply_text(
                "ℹ️ Сначала выберите проект: /project switch <имя_проекта>"
            )
            return False
        return True
