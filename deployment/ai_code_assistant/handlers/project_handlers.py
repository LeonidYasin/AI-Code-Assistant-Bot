import logging
import re
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters
from typing import Dict, Any, Optional
import json

from core.project.manager import ProjectManager
from core.ai.project_ai import ProjectAI

logger = logging.getLogger(__name__)


class ProjectHandlers:
    def __init__(self, llm_client):
        self.llm = llm_client
        self.project_managers: Dict[int, ProjectManager] = {}
        self.project_ais: Dict[int, ProjectAI] = {}

    def get_project_manager(self, chat_id: int) -> ProjectManager:
        """Get or create project manager for chat"""
        if chat_id not in self.project_managers:
            self.project_managers[chat_id] = ProjectManager()
            self.project_ais[chat_id] = ProjectAI(self.llm, self.project_managers[chat_id])
        return self.project_managers[chat_id]

    def get_project_ai(self, chat_id: int) -> ProjectAI:
        """Get or create project AI for chat"""
        if chat_id not in self.project_ais:
            self.get_project_manager(chat_id)  # This will create both
        return self.project_ais[chat_id]

    async def handle_project_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle project-related commands"""
        chat_id = update.effective_chat.id
        command_text = update.message.text
        command_parts = command_text.split()
        
        # Debug output
        print("\n" + "="*50)
        print(f"[DEBUG] handle_project_command")
        print(f"Command text: {command_text}")
        print(f"Command parts: {command_parts}")
        print("="*50 + "\n")
        
        if not command_parts:
            await update.message.reply_text("❌ Неверная команда. Используйте /help для справки.")
            return
            
        command = command_parts[0].lower()
        args = command_parts[1:] if len(command_parts) > 1 else []
        
        # Debug output
        print("\n" + "="*50)
        print(f"[DEBUG] Command: {command}")
        print(f"Args: {args}")
        print("="*50 + "\n")
        
        try:
            if command == "/project" or command == "project":
                if not args:
                    await self._handle_project_info(update, context)
                elif args[0].lower() == "create" and len(args) > 1:
                    await self._handle_project_create(update, context, args[1])
                elif args[0].lower() == "switch" and len(args) > 1:
                    await self._handle_project_switch(update, context, args[1])
                elif args[0].lower() == "list":
                    # Handle project list command
                    projects = self.get_project_manager(chat_id).list_projects()
                    if not projects:
                        response = "ℹ️ У вас пока нет созданных проектов."
                    else:
                        response = "📂 Ваши проекты:\n" + "\n".join([
                            f"- {i+1}. {p['name']} (путь: {p['path']})" 
                            for i, p in enumerate(projects)
                        ])
                    await update.message.reply_text(response)
                else:
                    await update.message.reply_text("❌ Неверная команда проекта. Используйте /help для справки.")
            elif command == "/list":
                await self._handle_list_files(update, context)
            elif command == "/run":
                await self._handle_run_script(update, context)
            elif command == "/analyze":
                await self._handle_analyze(update, context)
            else:
                await update.message.reply_text("❌ Неизвестная команда. Используйте /help для списка команд.")
                
        except Exception as e:
            logger.error(f"Error in project command {command}: {e}", exc_info=True)
            await update.message.reply_text(f"⚠️ Произошла ошибка: {str(e)}")

    async def _log_bot_response(self, chat_id: int, message: str) -> None:
        """Log bot response to console"""
        logger.info(f"[BOT RESPONSE to {chat_id}]\n{message}")
        print("\n" + "="*50)
        print(f"BOT RESPONSE to {chat_id}:")
        print("-"*50)
        print(message)
        print("="*50 + "\n")

    async def _send_message(self, chat_id: int, text: str, **kwargs) -> None:
        """Send message and log it to console"""
        from telegram import Bot
        bot = Bot(token=context.bot.token)
        await bot.send_message(chat_id=chat_id, text=text, **kwargs)
        await self._log_bot_response(chat_id, text)

    async def handle_project_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle natural language project requests"""
        chat_id = update.effective_chat.id
        message_text = update.message.text.strip()
        
        # Log incoming message
        logger.info(f"[USER MESSAGE from {chat_id}] {message_text}")
        print("\n" + "="*50)
        print(f"USER MESSAGE from {chat_id}:")
        print("-"*50)
        print(message_text)
        print("="*50 + "\n")
        
        try:
            project_ai = self.get_project_ai(chat_id)
            action = await project_ai._determine_action(message_text)
            
            # Log determined action
            logger.info(f"[DETERMINED ACTION] {action}")
            print("\n" + "="*50)
            print("DETERMINED ACTION:")
            print("-"*50)
            print(json.dumps(action, indent=2, ensure_ascii=False))
            print("="*50 + "\n")
            
            if action["action"] == "unknown":
                response = "🤔 Не удалось понять ваш запрос. Пожалуйста, уточните, что вы хотите сделать."
                await update.message.reply_text(response)
                await self._log_bot_response(chat_id, response)
                return
                
            if action.get("needs_confirmation", False):
                # Store the pending action in user_data for confirmation
                context.user_data["pending_action"] = action
                keyboard = [
                    ["✅ Да", "❌ Нет"]
                ]
                reply_markup = {"keyboard": keyboard, "one_time_keyboard": True, "resize_keyboard": True}
                response = action.get('confirmation_message', 'Подтвердите действие:')
                await update.message.reply_text(response, reply_markup=reply_markup)
                await self._log_bot_response(chat_id, response)
            else:
                # Execute action immediately if no confirmation needed
                await self._execute_action(update, context, action)
                
        except Exception as e:
            error_msg = f"⚠️ Произошла ошибка при обработке запроса: {str(e)}"
            logger.error(f"Error processing project message: {e}", exc_info=True)
            await update.message.reply_text(error_msg)
            await self._log_bot_response(chat_id, error_msg)
            
    async def test_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Test command to simulate bot responses"""
        chat_id = update.effective_chat.id
        test_commands = [
            "/project list",
            "Покажи мои проекты",
            "Создай проект TestProject",
            "Переключись на проект TestProject",
            "Покажи файлы в проекте"
        ]
        
        response = "🧪 Доступные тестовые команды:\n\n"
        for i, cmd in enumerate(test_commands, 1):
            response += f"{i}. `{cmd}`\n"
            
        response += "\nОтправьте номер команды для тестирования."
        
        # Store test commands in context
        context.user_data["test_commands"] = test_commands
        
        await update.message.reply_text(response, parse_mode="Markdown")
        await self._log_bot_response(chat_id, response)
            
    async def handle_confirmation(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle user confirmation response or test command selection"""
        chat_id = update.effective_chat.id
        user_response = update.message.text.lower()
        
        # Check if this is a test command selection
        if "test_commands" in context.user_data and user_response.isdigit():
            index = int(user_response) - 1
            test_commands = context.user_data["test_commands"]
            
            if 0 <= index < len(test_commands):
                test_cmd = test_commands[index]
                logger.info(f"[TEST COMMAND SELECTED] {test_cmd}")
                print(f"\n[TEST] Executing command: {test_cmd}\n")
                
                # Simulate message with the test command
                update.message.text = test_cmd
                await self.handle_project_message(update, context)
                return
        
        # Handle confirmation response
        pending_action = context.user_data.get("pending_action")
        if not pending_action:
            await update.message.reply_text("Нет активных действий для подтверждения.")
            return
            
        if user_response in ["да", "yes", "подтверждаю", "✅ да"]:
            await self._execute_action(update, context, pending_action)
        else:
            response = "❌ Действие отменено."
            await update.message.reply_text(response)
            await self._log_bot_response(chat_id, response)
            
        # Clear the pending action
        if "pending_action" in context.user_data:
            del context.user_data["pending_action"]
            
    async def _execute_action(self, update: Update, context: ContextTypes.DEFAULT_TYPE, action: Dict[str, Any]) -> None:
        """Execute the specified action"""
        chat_id = update.effective_chat.id
        project_manager = self.get_project_manager(chat_id)
        project_ai = self.get_project_ai(chat_id)
        
        # Log action being executed
        logger.info(f"[EXECUTING ACTION] {action}")
        print("\n" + "="*50)
        print("EXECUTING ACTION:")
        print("-"*50)
        print(json.dumps(action, indent=2, ensure_ascii=False))
        print("="*50 + "\n")
        
        try:
            action_type = action["action"]
            
            if action_type == "create_project":
                await self._handle_project_create(update, context, action["project_name"])
            elif action_type == "switch_project":
                await self._handle_project_switch(update, context, action["project_name"])
            elif action_type == "list_projects":
                projects = project_manager.list_projects()
                if not projects:
                    response = "ℹ️ У вас пока нет созданных проектов."
                    await update.message.reply_text(response)
                    await self._log_bot_response(chat_id, response)
                    return
                    
                projects_list = ["📂 Ваши проекты:\n"]
                for i, project in enumerate(projects, 1):
                    projects_list.extend([
                        f"{i}. {project['name']}",
                        f"   📍 Путь: {project['path']}",
                        f"   📅 Создан: {project['created_at']}",
                        f"   📊 Размер: {project['size']}\n"
                    ])
                
                response = "\n".join(projects_list)
                await update.message.reply_text(response)
                await self._log_bot_response(chat_id, response)
                
                # Add quick actions
                keyboard = []
                for project in projects[:3]:  # Show first 3 projects as quick actions
                    keyboard.append([f"📂 {project['name']}"])
                
                if keyboard:
                    reply_markup = {
                        "keyboard": keyboard,
                        "resize_keyboard": True,
                        "one_time_keyboard": True
                    }
                    await update.message.reply_text(
                        "Выберите проект для работы:",
                        reply_markup=reply_markup
                    )
                
            elif action_type == "list_files":
                await self._handle_list_files(update, context)
            elif action_type == "analyze_code" and "code" in action:
                await update.message.reply_text("🔍 Анализирую код...")
                success, response = await project_ai.process_request(f"analyze: {action['code']}")
                await update.message.reply_text(response, parse_mode="Markdown")
            else:
                # Fall back to processing with the AI
                success, response = await project_ai.process_request(update.message.text)
                await update.message.reply_text(response, parse_mode="Markdown")
                
        except Exception as e:
            logger.error(f"Error executing action {action}: {e}", exc_info=True)
            await update.message.reply_text(f"⚠️ Ошибка при выполнении действия: {str(e)}")

    async def _handle_project_info(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle project info command"""
        project_manager = self.get_project_manager(update.effective_chat.id)
        project_info = project_manager.get_project_info()
        
        if not project_info.get('current_project'):
            await update.message.reply_text(
                "ℹ️ Активный проект не выбран.\n"
                "Используйте /project create <имя> для создания нового проекта.\n"
                "Или /project list для просмотра существующих проектов."
            )
            return
            
        
        response = (
            f"📂 Текущий проект: {project_manager.current_project.name}\n"
            f"📊 Файлов в проекте: {project_manager.current_project.file_count}\n\n"
            "Доступные команды:\n"
            "/list - Показать файлы проекта\n"
            "/read <файл> - Показать содержимое файла\n"
            "/analyze <код> - Проанализировать код\n"
            "/run <скрипт> - Запустить Python скрипт\n"
            "\nИли просто напишите, что нужно сделать, например:\n"
            "\"Создай файл main.py с Hello World\"\n"
            "\"Запусти скрипт test.py\"\n"
            "\"Проанализируй этот код...\""
        )
        
        await update.message.reply_text(response)

    async def _handle_project_list(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
        """Handle project list command
        
        Returns:
            str: Formatted list of projects or error message
        """
        chat_id = update.effective_chat.id
        project_manager = self.get_project_manager(chat_id)
        
        try:
            projects = project_manager.list_projects()
            print(f"DEBUG: Got projects: {projects}")  # Debug output
            
            if not projects:
                return "ℹ️ Нет доступных проектов. Используйте /project create <имя> для создания проекта."
                
            projects_list = "📂 Доступные проекты:\n"
            for i, project in enumerate(projects, 1):
                project_name = project.get('name', 'Неизвестный проект')
                project_size = project.get('size', '0 B')
                project_files = project.get('file_count', 0)
                
                projects_list += f"{i}. {project_name} ({project_size}, {project_files} файлов)"
                if project.get('is_current'):
                    projects_list += " (текущий)"
                projects_list += "\n"
                
            return projects_list
            
        except Exception as e:
            error_msg = f"❌ Ошибка при получении списка проектов: {str(e)}"
            print(f"DEBUG: {error_msg}")
            logger.error(error_msg, exc_info=True)
            return error_msg
        
    async def _handle_project_create(self, update: Update, context: ContextTypes.DEFAULT_TYPE, project_name: str) -> None:
        """Handle project creation
        
        Args:
            update: Telegram update object
            context: Telegram context
            project_name: Name of the project to create
        """
        chat_id = update.effective_chat.id
        project_manager = self.get_project_manager(chat_id)
        
        try:
            # Create the project
            project_path = project_manager.create_project(project_name)
            if project_path:
                await update.message.reply_text(f"✅ Проект '{project_name}' успешно создан в {project_path}")
            else:
                await update.message.reply_text(f"❌ Не удалось создать проект '{project_name}'. Возможно, он уже существует.")
        except Exception as e:
            logger.error(f"Error creating project: {e}", exc_info=True)
            await update.message.reply_text(f"❌ Ошибка при создании проекта: {str(e)}")

    async def _handle_list_files(self, update: Update, context: ContextTypes.DEFAULT_TYPE, path: str = None) -> None:
        """List files in the project with optional subdirectory path"""
        chat_id = update.effective_chat.id
        project_manager = self.get_project_manager(chat_id)
        
        if not project_manager.current_project:
            await update.message.reply_text(
                "ℹ️ Сначала выберите проект с помощью /project switch <имя_проекта>"
            )
            return
            
        try:
            # If path is provided, use it as subdirectory
            base_path = Path(project_manager.current_project)
            target_path = base_path / path if path else base_path
            target_path = target_path.resolve()
            
            # Security check: ensure we're still within the project directory
            if not str(target_path).startswith(str(base_path)):
                await update.message.reply_text("❌ Ошибка безопасности: недопустимый путь")
                return
                
            if not target_path.exists():
                await update.message.reply_text("❌ Указанный путь не существует")
                return
                
            # Get directory contents
            dirs = []
            files = []
            
            for item in sorted(target_path.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
                if item.is_file():
                    size = item.stat().st_size
                    files.append(f"📄 {item.name} ({self._format_size(size)})")
                else:
                    file_count = sum(1 for _ in item.glob('**/*') if _.is_file())
                    dirs.append(f"📁 {item.name}/ ({file_count} файлов)")
            
            # Build response message
            rel_path = target_path.relative_to(base_path)
            response = [f"📂 Содержимое: /{rel_path if rel_path != Path('.') else ''}"]
            
            if dirs:
                response.append("\n📁 Папки:")
                response.extend(dirs)
            
            if files:
                response.append("\n📄 Файлы:")
                response.extend(files)
            
            if not (dirs or files):
                response.append("\nℹ️ Папка пуста")
            
            # Send the response
            await update.message.reply_text("\n".join(response))
            
        except Exception as e:
            logger.error(f"Error listing files: {e}", exc_info=True)
            await update.message.reply_text(f"⚠️ Ошибка при получении списка файлов: {str(e)}")
            
    def _format_size(self, size_bytes: int) -> str:
        """Convert size in bytes to human-readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0 or unit == 'GB':
                break
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} {unit}"

    async def _handle_run_script(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Run a Python script"""
        chat_id = update.effective_chat.id
        
        if not context.args:
            await update.message.reply_text("Пожалуйста, укажите имя скрипта. Например: /run script.py")
            return
            
        script_name = context.args[0]
        project_ai = self.get_project_ai(chat_id)
        
        success, response = await project_ai.process_request(f"Выполни скрипт {script_name}")
        await update.message.reply_text(response, parse_mode="Markdown")

    async def _handle_analyze(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Analyze code"""
        chat_id = update.effective_chat.id
        project_ai = self.get_project_ai(chat_id)
        
        code = update.message.text.replace('/analyze', '').strip()
        if not code:
            await update.message.reply_text("Пожалуйста, укажите код для анализа после команды /analyze")
            return
            
        try:
            success, response = await project_ai.process_request(f"analyze: {code}")
            
            # Split long messages to avoid 'Message is too long' error
            max_length = 4096
            for i in range(0, len(response), max_length):
                await update.message.reply_text(
                    response[i:i+max_length],
                    parse_mode="Markdown"
                )
                # Add small delay to avoid rate limiting
                import asyncio
                await asyncio.sleep(0.5)
        except Exception as e:
            logger.error(f"Error in _handle_analyze: {e}", exc_info=True)
            await update.message.reply_text(f"Произошла ошибка при анализе кода: {str(e)}")
    
    async def _handle_analyze_project(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Analyze the current project structure and contents"""
        # Check if running in CLI mode (update is None or doesn't have effective_chat)
        is_cli = update is None or not hasattr(update, 'effective_chat')
        
        if is_cli:
            chat_id = 0
            reply_func = print
        else:
            chat_id = update.effective_chat.id
            reply_func = update.message.reply_text
            
        project_manager = self.get_project_manager(chat_id)
        
        if not project_manager.current_project:
            error_msg = "❌ Сначала выберите проект с помощью /project switch <имя_проекта>"
            await reply_func(error_msg) if not is_cli else print(error_msg)
            return (False, error_msg) if is_cli else None
            
        try:
            # Get project path
            project_path = project_manager.get_project_path(project_manager.current_project)
            if not project_path or not project_path.exists():
                error_msg = f"❌ Не удалось найти директорию проекта: {project_path}"
                await reply_func(error_msg) if not is_cli else print(error_msg)
                return (False, error_msg) if is_cli else None
                
            # Initialize project analyzer
            from core.project.analyzer import ProjectAnalyzer
            analyzer = ProjectAnalyzer(project_path)
            
            # Analyze project
            analysis = analyzer.analyze()
            
            # Format results
            response = (
                f"📊 *Анализ проекта: {project_manager.current_project}*\n\n"
                f"📂 *Директория:* `{project_path}`\n"
                f"📝 *Всего файлов:* {analysis.get('total_files', 0)}\n"
                f"📦 *Размер проекта:* {self._format_size(analysis.get('total_size', 0))}\n\n"
                f"📋 *Языки программирования:*\n"
            )
            
            # Add language statistics
            for lang, count in analysis.get('languages', {}).items():
                response += f"- {lang}: {count} файлов\n"
                
            # Add main files and folders
            response += "\n📂 *Основные файлы и папки:*\n"
            for item in analysis.get('main_items', [])[:10]:  # Show top 10
                item_path = item['path'].relative_to(project_path)
                response += f"- `{item_path}` ({self._format_size(item['size'])})\n"
                
            # Add analysis details
            response += "\n🔍 *Детали анализа:*\n"
            response += analysis.get('analysis_details', 'Нет дополнительной информации')
            
            if is_cli:
                # In CLI mode, just return the response
                return True, response
                
            # In bot mode, handle message splitting
            max_length = 4000
            if len(response) > max_length:
                # Split by double newlines to keep paragraphs together
                chunks = []
                current_chunk = ""
                
                for paragraph in response.split('\n\n'):
                    if len(current_chunk) + len(paragraph) + 2 > max_length and current_chunk:
                        chunks.append(current_chunk)
                        current_chunk = paragraph
                    else:
                        if current_chunk:
                            current_chunk += '\n\n' + paragraph
                        else:
                            current_chunk = paragraph
                
                if current_chunk:
                    chunks.append(current_chunk)
                
                # Send each chunk as a separate message
                for i, chunk in enumerate(chunks, 1):
                    await reply_func(
                        f"*[Часть {i}/{len(chunks)}]*\n{chunk}",
                        parse_mode="Markdown"
                    )
            else:
                await reply_func(response, parse_mode="Markdown")
                
        except Exception as e:
            error_msg = f"❌ Не удалось проанализировать проект. Ошибка: {str(e)}"
            logger.error(f"Error in _handle_analyze_project: {e}", exc_info=True)
            if is_cli:
                return False, error_msg
            await reply_func(error_msg)
    
    async def error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle errors in the telegram bot."""
        logger.error("Exception while handling an update:", exc_info=context.error)
        
        # Log the error to the console
        error_msg = f"An error occurred: {context.error}"
        print("\n" + "="*50)
        print("ERROR:")
        print("-"*50)
        print(error_msg)
        print("="*50 + "\n")
        
        # Try to notify the user if possible
        try:
            if update and hasattr(update, 'effective_message'):
                await update.effective_message.reply_text(
                    "⚠️ Произошла ошибка при обработке запроса. Пожалуйста, попробуйте еще раз."
                )
        except Exception as e:
            logger.error(f"Error while notifying user: {e}", exc_info=True)



async def register_project_handlers(application, llm_client):
    """Register project handlers with the application"""
    logger.info("Registering project handlers...")
    
    try:
        # Initialize handlers
        project_handlers = ProjectHandlers(llm_client)
        
        # Store handlers in bot_data for later use (only if we have an application)
        if application is not None and hasattr(application, 'bot_data'):
            application.bot_data['project_handlers'] = project_handlers
        
        # Register command handlers (only if we have an application)
        if application is not None:
            application.add_handler(CommandHandler("project", project_handlers.handle_project_command))
            
            # Register message handlers
            application.add_handler(MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                project_handlers.handle_project_message
            ))
        
        # Register available command handlers (only if we have an application)
        if application is not None:
            if hasattr(project_handlers, '_handle_analyze'):
                application.add_handler(CommandHandler("analyze", project_handlers._handle_analyze))
                
            if hasattr(project_handlers, '_handle_analyze_project'):
                application.add_handler(CommandHandler("analyze_project", project_handlers._handle_analyze_project))
                
            if hasattr(project_handlers, '_handle_list_files'):
                application.add_handler(CommandHandler("list", project_handlers._handle_list_files))
                
            if hasattr(project_handlers, '_handle_run_script'):
                application.add_handler(CommandHandler("run", project_handlers._handle_run_script))
                
            if hasattr(project_handlers, '_handle_project_info'):
                application.add_handler(CommandHandler("project_info", project_handlers._handle_project_info))
        
        logger.info("Project handlers registered")
        return project_handlers
    except Exception as e:
        logger.error(f"Error registering project handlers: {e}", exc_info=True)
        raise

    # Confirmation handler with emoji support
    if application is not None:
        application.add_handler(MessageHandler(
            filters.Regex(r'^\s*(?:[\u2705\u274c]\s*)?(?:да|нет|yes|no|\d+)\s*$') & filters.Regex(r'(?i)^[^a-z]*(?:да|нет|yes|no)'),
            project_handlers.handle_confirmation
        ))
        
        # Register error handler
        application.add_error_handler(project_handlers.error_handler)
    
    logger.info("Project handlers registered")
    
    return project_handlers
