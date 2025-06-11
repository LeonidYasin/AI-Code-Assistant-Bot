from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, CallbackContext
from typing import Dict, Any, Optional, List
import logging
from pathlib import Path
import json

from core.bot.types import CommandInfo, ModuleInfo
from core.project.manager import ProjectManager

logger = logging.getLogger(__name__)

class ProjectHandler:
    """Handler for project-related commands"""
    
    def __init__(self, project_manager: ProjectManager):
        """Initialize the project handler.
        
        Args:
            project_manager: Instance of ProjectManager
        """
        self.project_manager = project_manager
    
    @classmethod
    def get_module_info(cls) -> ModuleInfo:
        """Get module information."""
        return ModuleInfo(
            name="Project Management",
            description="Manage code projects",
            commands=[
                CommandInfo(
                    command="project",
                    description="Управление проектами",
                    handler=cls.handle_project_command,
                    usage=(
                        "/project list - Список всех проектов\n"
                        "/project create <имя> - Создать новый проект\n"
                        "/project switch <имя> - Переключиться на проект\n"
                        "/project info - Информация о текущем проекте"
                    )
                ),
            ],
        )
    
    @classmethod
    async def handle_project_command(
        cls, 
        update: Update, 
        context: CallbackContext
    ) -> None:
        """Handle project commands.
        
        Args:
            update: The incoming update.
            context: The callback context.
        """
        # Debug output
        print("\n" + "="*50)
        print("[DEBUG] handle_project_command")
        print(f"Message text: {update.message.text}")
        print(f"Context args: {context.args}")
        print("="*50 + "\n")
        
        # Get or create handler instance
        if not context.bot_data.get('project_handler'):
            from core.project.manager import ProjectManager
            context.bot_data['project_handler'] = cls(ProjectManager())
            
        handler = context.bot_data['project_handler']
        
        # If no args, try to split the message text
        if not context.args and update.message.text:
            # Split the message text into parts
            parts = update.message.text.split()
            if len(parts) > 1:
                subcommand = parts[1].lower()
                args = parts[2:] if len(parts) > 2 else []
                return await cls._handle_subcommand(handler, subcommand, args, update, context)
        
        if not context.args:
            await update.message.reply_text(
                "❌ Не указана команда. Используйте /help project для справки."
            )
            return
            
        subcommand = context.args[0].lower()
        args = context.args[1:]
        
        # Handle the subcommand
        return await cls._handle_subcommand(handler, subcommand, args, update, context)
    
    @classmethod
    async def _handle_subcommand(cls, handler, subcommand, args, update, context):
        """Handle a project subcommand."""
        # Debug output
        print("\n" + "="*50)
        print(f"[DEBUG] _handle_subcommand")
        print(f"Subcommand: {subcommand}")
        print(f"Args: {args}")
        print("="*50 + "\n")
        
        handlers = {
            'list': {
                'handler': handler._handle_list,
                'help': '📋 Показать список всех проектов',
                'usage': '/project list'
            },
            'create': {
                'handler': handler._handle_create,
                'help': '🆕 Создать новый проект',
                'usage': '/project create <имя>'
            },
            'switch': {
                'handler': handler._handle_switch,
                'help': '🔄 Переключиться на другой проект',
                'usage': '/project switch <имя>'
            },
            'info': {
                'handler': handler._handle_info,
                'help': 'ℹ️ Показать информацию о текущем проекте',
                'usage': '/project info'
            },
        }
        
        handler_info = handlers.get(subcommand)
        if handler_info:
            try:
                await handler_info['handler'](update, context, *args)
            except Exception as e:
                logger.error(f"Error in {subcommand} handler: {e}", exc_info=True)
                await update.message.reply_text(
                    f"❌ Произошла ошибка при выполнении команды {subcommand}.\n"
                    f"Ошибка: {str(e)}"
                )
        else:
            help_text = [
                f"❌ Неизвестная команда проекта: {subcommand}.\n",
                "📚 Доступные команды проекта:",
                *[f"• {h['help']}\n  Использование: {h['usage']}" for h in handlers.values()],
                "\nℹ️ Используйте /help project для полной справки."
            ]
            await update.message.reply_text("\n".join(help_text))
    
    async def _handle_list(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle project list command"""
        try:
            success, result = self.project_manager.list_projects()
            if not success:
                await update.message.reply_text(f"❌ Ошибка при получении списка проектов: {result}")
                return
                
            if not result:
                await update.message.reply_text("ℹ️ У вас пока нет созданных проектов.")
                return
                
            projects_list = ["📂 Ваши проекты:"]
            for i, project in enumerate(result, 1):
                project_name = project.get('name', 'Без имени')
                project_path = project.get('path', 'неизвестный путь')
                project_size = project.get('size', '0 Б')
                project_files = project.get('file_count', 0)
                
                project_info = [
                    f"{i}. {project_name}",
                    f"   📍 Путь: {project_path}",
                    f"   📊 Размер: {project_size}",
                    f"   📝 Файлов: {project_files}"
                ]
                projects_list.append("\n".join(project_info))
            
            response = "\n\n".join(projects_list)
            await update.message.reply_text(response)
            
        except Exception as e:
            logger.error(f"Error in _handle_list: {e}", exc_info=True)
            await update.message.reply_text("❌ Произошла ошибка при получении списка проектов. Пожалуйста, попробуйте снова.")
            if project.get('is_current'):
                projects_list += " (текущий)"
            projects_list += "\n"
            
        await update.message.reply_text(projects_list)
    
    async def _handle_create(self, update: Update, context: ContextTypes.DEFAULT_TYPE, *args) -> None:
        """Handle project create command"""
        if not args:
            await update.message.reply_text("❌ Укажите имя проекта: /project create <имя>")
            return
            
        project_name = ' '.join(args)
        try:
            project_path = self.project_manager.create_project(project_name)
            await update.message.reply_text(f"✅ Проект создан: {project_path}")
        except ValueError as e:
            await update.message.reply_text(f"❌ Ошибка: {str(e)}")
        except Exception as e:
            logger.error(f"Error creating project: {e}", exc_info=True)
            await update.message.reply_text(f"❌ Ошибка при создании проекта: {str(e)}")
    
    async def _handle_switch(self, update: Update, context: ContextTypes.DEFAULT_TYPE, *args) -> None:
        """Handle project switch command"""
        if not args:
            await update.message.reply_text("❌ Укажите имя проекта: /project switch <имя>")
            return
            
        project_name = ' '.join(args)
        chat_id = update.effective_chat.id
        
        # Debug output
        print(f"\n[DEBUG] Switching to project: {project_name} for chat {chat_id}")
        
        # Try to switch to the project
        if not self.project_manager.switch_project(project_name):
            await update.message.reply_text(f"❌ Проект не найден: {project_name}")
            return
        
        # Store the active project in the context
        if not hasattr(context, 'active_project'):
            context.active_project = {}
        context.active_project[chat_id] = project_name
        
        # Also store in bot_data for compatibility
        if hasattr(context, 'bot_data') and context.bot_data is not None:
            if not isinstance(context.bot_data, dict):
                if not hasattr(context.bot_data, 'active_project'):
                    context.bot_data.active_project = {}
                context.bot_data.active_project[chat_id] = project_name
            else:
                if 'active_project' not in context.bot_data:
                    context.bot_data['active_project'] = {}
                context.bot_data['active_project'][chat_id] = project_name
        
        await update.message.reply_text(f"✅ Переключено на проект: {project_name}")
        
        # Debug: Print current state
        print("\n[DEBUG] After switching:")
        print(f"context.active_project: {getattr(context, 'active_project', {})}")
        if hasattr(context, 'bot_data'):
            print(f"bot_data.active_project: {getattr(context.bot_data, 'active_project', getattr(context.bot_data, 'get', lambda x,y: y)('active_project', 'N/A'))}")
    
    async def _handle_info(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle project info command"""
        chat_id = update.effective_chat.id
        project_name = None
        project_info = None
        
        # Try to get active project from context.active_project first
        if hasattr(context, 'active_project') and context.active_project:
            if chat_id in context.active_project:
                project_name = context.active_project[chat_id]
                print(f"Found active project in context.active_project: {project_name}")
        
        # Fallback to bot_data if not found in context.active_project
        if not project_name and hasattr(context, 'bot_data') and context.bot_data:
            if not isinstance(context.bot_data, dict):
                if hasattr(context.bot_data, 'active_project') and hasattr(context.bot_data.active_project, 'get'):
                    project_name = context.bot_data.active_project.get(chat_id)
                    print(f"Found active project in context.bot_data.active_project: {project_name}")
            elif 'active_project' in context.bot_data and context.bot_data['active_project']:
                if chat_id in context.bot_data['active_project']:
                    project_name = context.bot_data['active_project'][chat_id]
                    print(f"Found active project in context.bot_data['active_project']: {project_name}")
        
        # If we have a project name, try to get its info
        if project_name:
            if not self.project_manager.switch_project(project_name):
                await update.message.reply_text(
                    "❌ Не удалось загрузить активный проект. "
                    "Попробуйте переключиться снова."
                )
                return
            
            # Get project info
            project_info = self.project_manager.get_project_info()
        
        # If we have project info, format and display it
        if project_info:
            info_text = (
                f"📋 Информация о проекте:\n"
                f"📁 Название: {project_info.get('name', project_name)}\n"
                f"📂 Путь: {project_info.get('path', '❌ Неизвестен')}\n"
                f"📝 Описание: {project_info.get('description', '❌ Отсутствует')}\n"
                f"📅 Создан: {project_info.get('created_at', '❌ Неизвестно')}"
            )
            await update.message.reply_text(info_text)
        else:
            # If we get here, no active project was found or couldn't get info
            await update.message.reply_text(
                "ℹ️ Активный проект не выбран.\n"
                "Используйте /project switch <имя> для выбора проекта."
            )
