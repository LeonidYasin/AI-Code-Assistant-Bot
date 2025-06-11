"""Handlers for natural language processing commands"""
import logging
from typing import Dict, Any
from telegram import Update
from telegram.ext import ContextTypes
from core.project.manager import CommandType, ProjectManager
from .commands import command_handler

logger = logging.getLogger(__name__)

@command_handler
def register_nlp_handlers(application):
    """Register natural language command handlers"""
    from telegram.ext import MessageHandler, filters
    # Add a message handler for all text messages that aren't commands
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, process_natural_language))
    
async def process_natural_language(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Process natural language commands"""
    if not context.args and not update.message.text:
        return "Пожалуйста, укажите команду для выполнения."
        
    # Get the full command text
    command = ' '.join(context.args) if context.args else update.message.text
    
    # Get project manager from context
    project_manager = context.bot_data.get('project_manager')
    if not project_manager:
        return "❌ Ошибка: ProjectManager не инициализирован"
    
    # Process the command
    result = project_manager.process_natural_language(command)
    if not result.get('success'):
        return f"❌ Ошибка: {result.get('error', 'Неизвестная ошибка')}"
    
    # Execute the command
    cmd_type = result.get('type')
    path = result.get('path', '')
    content = result.get('content', '')
    
    try:
        if cmd_type == CommandType.CREATE_FILE:
            success, message = project_manager.create_file(path, content)
            return message
            
        elif cmd_type == CommandType.READ_FILE:
            success, content = project_manager.read_file(path)
            if not success:
                return f"❌ {content}"
            return f"📄 Содержимое файла {path}:\n\n```\n{content}\n```"
            
        elif cmd_type == CommandType.UPDATE_FILE:
            # For update, we need to get existing content first
            success, current_content = project_manager.read_file(path)
            if not success:
                return f"❌ Не удалось прочитать файл: {current_content}"
                
            # Here you could implement a diff/patch mechanism
            # For now, just replace the content
            success, message = project_manager.create_file(path, content)
            return message
            
        elif cmd_type == CommandType.DELETE_FILE:
            # Implement file deletion with confirmation
            return "⚠️ Удаление файлов пока не реализовано. Используйте команду /delete"
            
        elif cmd_type == CommandType.LIST_FILES:
            success, result = project_manager.list_files(path)
            if not success:
                return f"❌ {result}"
                
            if not result:
                return f"📂 Директория {path} пуста"
                
            files_list = ["📂 Содержимое директории:"]
            for item in result:
                item_type = "📁" if item['type'] == 'directory' else "📄"
                size = f" ({item['size']} bytes)" if item['type'] == 'file' else ""
                files_list.append(f"{item_type} {item['path']}{size}")
                
            return "\n".join(files_list)
            
        elif cmd_type == CommandType.ANALYZE_CODE:
            success, result = project_manager.analyze_code(path)
            if not success:
                return f"❌ {result}"
                
            return f"🔍 Анализ кода {path}:\n\n{result}"
            
        elif cmd_type == CommandType.RUN_CODE:
            return "⚠️ Выполнение кода пока не реализовано. Используйте команду /run"
            
        else:
            return f"❌ Неизвестная команда: {cmd_type}"
            
    except Exception as e:
        logger.error(f"Error executing command: {e}", exc_info=True)
        return f"❌ Ошибка при выполнении команды: {str(e)}"
