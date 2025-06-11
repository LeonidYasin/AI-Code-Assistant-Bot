"""Natural Language Processing for command conversion"""
import logging
import json
import sys
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
from telegram import Update
from telegram.ext import ContextTypes
from core.llm.client import llm_client

logger = logging.getLogger(__name__)

class NLPProcessor:
    """Processes natural language commands and converts them to strict commands"""
    
    def __init__(self):
        self.command_map = {
            'create_project': self._handle_create_project,
            'create_file': self._handle_create_file,
            'list_projects': self._handle_list_projects,
            'switch_project': self._handle_switch_project,
            'list_files': self._handle_list_files,
            'view_file': self._handle_view_file,
            'run_code': self._handle_run_code,
            'analyze_code': self._handle_analyze_code,
            'analyze_project': self._handle_analyze_project,
        }
    
    async def process_command(self, text: str, context: ContextTypes.DEFAULT_TYPE) -> Tuple[bool, str]:
        """Process natural language command and return (success, response)"""
        try:
            # Initialize active_projects in bot_data if it doesn't exist
            if 'active_projects' not in context.bot_data:
                context.bot_data['active_projects'] = {}
            
            # Get or initialize project manager
            if 'project_manager' not in context.bot_data:
                from core.project.manager import ProjectManager
                context.bot_data['project_manager'] = ProjectManager()
            
            # Get chat ID or use default for CLI
            chat_id = getattr(context, '_chat_id', 0)
            chat_id_str = str(chat_id)
            
            # Initialize active projects in instance if needed
            if not hasattr(self, '_active_projects'):
                self._active_projects = {}
            
            # Sync active projects between context and instance
            if chat_id_str in context.bot_data['active_projects']:
                self._active_projects[chat_id_str] = context.bot_data['active_projects'][chat_id_str]
            elif chat_id_str in self._active_projects:
                context.bot_data['active_projects'][chat_id_str] = self._active_projects[chat_id_str]
            
            # Sync with project manager's current project
            project_manager = context.bot_data['project_manager']
            if project_manager.current_project and chat_id_str not in context.bot_data['active_projects']:
                context.bot_data['active_projects'][chat_id_str] = project_manager.current_project
                self._active_projects[chat_id_str] = project_manager.current_project
            
            current_project = self._active_projects.get(chat_id_str)
            logger.info(f"Processing natural language input: {text}")
            logger.info(f"Current project for chat {chat_id}: {current_project}")
            logger.debug(f"Project manager current project: {project_manager.current_project}")
            logger.debug(f"Active projects in context: {context.bot_data['active_projects']}")
            logger.debug(f"Active projects: {context.bot_data['active_projects']}")
            
            # Prepare the prompt for the LLM
            prompt = self._build_prompt(text, current_project)
            
            # Show the prompt being sent to AI
            prompt_display = f"🤖 Отправляю запрос в ИИ:\n```\n{prompt}\n```"
            await self._send_message(context, prompt_display)
            
            # Get response from LLM
            response = llm_client.call(prompt, is_json=True)
            
            # Show the raw AI response
            response_display = f"📩 Получен ответ от ИИ:\n```json\n{response}\n```"
            await self._send_message(context, response_display)
            
            try:
                command_data = json.loads(response)
                command = command_data.get('command')
                params = command_data.get('params', {})
                
                # Show parsed command information
                command_info = (
                    f"🔍 Распознана команда: `{command}`\n"
                    f"📋 Параметры:\n```json\n{json.dumps(params, indent=2, ensure_ascii=False)}\n```"
                )
                await self._send_message(context, command_info)
                
                if not command or command not in self.command_map:
                    error_msg = f"❌ Неизвестная команда: {command}"
                    logger.error(error_msg)
                    await self._send_message(context, error_msg)
                    return False, error_msg
                
                # Ask for confirmation before executing
                confirmation = await self._ask_confirmation(
                    context,
                    f"Выполнить команду `{command}` с указанными параметрами?"
                )
                
                if not confirmation:
                    msg = "❌ Команда отменена пользователем"
                    await self._send_message(context, msg)
                    return False, msg
                
                # Execute the command
                logger.info(f"Executing command: {command} with params: {params}")
                execution_msg = f"⚡ Выполняю команду `{command}`..."
                await self._send_message(context, execution_msg)
                
                result = await self.command_map[command](context, **params)
                
                # Log and show the result
                if isinstance(result, tuple) and len(result) == 2:
                    success, message = result
                    result_msg = f"✅ {message}" if success else f"❌ {message}"
                else:
                    success = True
                    result_msg = "✅ Команда выполнена успешно"
                
                await self._send_message(context, result_msg)
                
                # Log without emojis to avoid encoding issues
                if isinstance(result, tuple) and len(result) == 2:
                    log_success, log_message = result
                    logger.info(f"Command completed - Success: {log_success}, Message: {log_message}")
                else:
                    logger.info(f"Command completed successfully: {result}")
                
                return success, result_msg
                
            except json.JSONDecodeError as e:
                error_msg = f"❌ Ошибка при разборе ответа ИИ: {str(e)}\n\nОтвет ИИ:\n```\n{response}\n```"
                await self._send_message(context, error_msg)
                logger.error(f"JSON decode error: {e}")
                return False, error_msg
                
        except Exception as e:
            error_msg = f"❌ Ошибка при обработке команды: {str(e)}"
            logger.error(f"Error in process_command: {e}", exc_info=True)
            await self._send_message(context, error_msg)
            return False, error_msg
            
    async def _send_message(self, context: ContextTypes.DEFAULT_TYPE, text: str) -> None:
        """Helper method to send a message to the user"""
        try:
            if hasattr(context, 'send_message'):
                await context.send_message(chat_id=context._chat_id, text=text, parse_mode='Markdown')
            elif hasattr(context, 'reply_text'):
                await context.reply_text(text=text, parse_mode='Markdown')
            else:
                print(f"\n[CLI MESSAGE]\n{text}\n")
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            print(f"\n[ERROR SENDING MESSAGE]\n{text}\n")
            
    async def _ask_confirmation(self, context: ContextTypes.DEFAULT_TYPE, question: str) -> bool:
        """Ask for user confirmation before executing a command"""
        # In non-interactive mode (like when running from command line with parameters),
        # we'll auto-confirm for simplicity
        is_interactive = hasattr(sys, 'stdin') and sys.stdin.isatty()
        
        if not hasattr(context, 'bot') or not hasattr(context, '_chat_id'):
            if is_interactive:
                # In interactive CLI mode, ask for confirmation
                print(f"\n{question} (y/n): ", end='', flush=True)
                try:
                    response = input().strip().lower()
                    return response in ('y', 'yes', 'д', 'да')
                except (EOFError, KeyboardInterrupt):
                    print("\n[INFO] Auto-confirming due to non-interactive mode")
                    return True
            else:
                # In non-interactive mode, auto-confirm
                print(f"\n[INFO] Auto-confirming: {question}")
                return True
            
        # In bot mode, send a confirmation message with buttons
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        
        keyboard = [
            [
                InlineKeyboardButton("✅ Да", callback_data="confirm_yes"),
                InlineKeyboardButton("❌ Нет", callback_data="confirm_no")
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        message = await context.bot.send_message(
            chat_id=context._chat_id,
            text=question,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
        # Store the message ID to handle the response
        if not hasattr(context, 'pending_confirmations'):
            context.pending_confirmations = {}
        context.pending_confirmations[message.message_id] = message
        
        # In a real bot, you'd use conversation handlers here
        # For now, we'll just return True to continue
        return True
    
    def _build_prompt(self, text: str, current_project: Optional[str] = None) -> str:
        """Build the prompt for the LLM"""
        context = f"Текущий проект: {current_project}" if current_project else "Активный проект не выбран"
        
        return f"""
Пользователь отправил запрос: {text}
Контекст: {context}

Проанализируй запрос и преобразуй его в команду и параметры.

Доступные команды:
1. create_project - Создать новый проект
   Параметры: project_name (название проекта)
   Пример: {{"command": "create_project", "params": {{"project_name": "мой_проект"}}}}

2. create_file - Создать файл
   Параметры: name (имя файла), content (содержимое)
   Пример: {{"command": "create_file", "params": {{"name": "main.py", "content": "print(\\"Hello, World!\\")"}}}}

3. list_projects - Показать список проектов
   Параметры: отсутствуют
   Пример: {{"command": "list_projects", "params": {{}}}}

4. switch_project - Переключиться на проект
   Параметры: project_name (название проекта)
   Пример: {{"command": "switch_project", "params": {{"project_name": "мой_проект"}}}}

5. list_files - Показать файлы в проекте
   Параметры: path (опционально, путь внутри проекта)
   Пример: {{"command": "list_files", "params": {{"path": "src"}}}}

6. view_file - Показать содержимое файла
   Параметры: file_path (путь к файлу)
   Пример: {{"command": "view_file", "params": {{"file_path": "src/main.py"}}}}

7. run_code - Выполнить код
   Параметры: code (код для выполнения)
   Пример: {{"command": "run_code", "params": {{"code": "print(1+1)"}}}}

8. analyze_code - Проанализировать код
   Параметры: code (код для анализа)
   Пример: {{"command": "analyze_code", "params": {{"code": "def test(): pass"}}}}

Важные замечания:
- Если в запросе упоминается файл, используй команду view_file
- Если запрашивается содержимое файла, используй view_file
- Если запрашивается список файлов, используй list_files
- Всегда указывай полный путь к файлу в параметре file_path
- Сохраняй контекст текущего проекта

Верни ответ в формате JSON с полями command и params.
"""

    # Command handlers
    async def _handle_view_file(self, context: ContextTypes.DEFAULT_TYPE, **kwargs) -> Tuple[bool, str]:
        """Handle view_file command
        
        Args:
            context: Bot context
            **kwargs: Should contain either 'path' or 'file_path' parameter with the file path
            
        Returns:
            Tuple[bool, str]: Success status and message
        """
        try:
            # Get the file path from either 'path' or 'file_path' parameter
            path = kwargs.get('path') or kwargs.get('file_path')
            
            if not path:
                return False, "❌ Не указан путь к файлу"
                
            # Get the current project
            active_projects = context.bot_data.get('active_projects', {})
            chat_id = getattr(context, '_chat_id', 0)
            current_project = active_projects.get(str(chat_id))
            
            if not current_project:
                return False, "❌ Активный проект не выбран. Сначала переключитесь на проект."
            
            # Build full path
            base_dir = os.path.join("projects", current_project)
            full_path = os.path.normpath(os.path.join(base_dir, path))
            
            # Security check: prevent directory traversal
            if not os.path.abspath(full_path).startswith(os.path.abspath(base_dir)):
                return False, "❌ Ошибка безопасности: недопустимый путь к файлу"
            
            # Check if file exists
            if not os.path.exists(full_path):
                return False, f"❌ Файл не найден: {file_path}"
            
            if not os.path.isfile(full_path):
                return False, f"❌ Указанный путь не является файлом: {file_path}"
            
            # Read file content with proper encoding
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Truncate long content for display
                max_length = 2000
                if len(content) > max_length:
                    content = content[:max_length] + "\n[... файл обрезан ...]"
                
                # Format the response
                response = (
                    f"📄 Содержимое файла {file_path} в проекте {current_project}:\n"
                    f"```\n{content}\n```"
                )
                return True, response
                
            except UnicodeDecodeError:
                return False, f"❌ Не удалось прочитать файл: {file_path} (неподдерживаемая кодировка)"
            
        except Exception as e:
            logger.error(f"Error in _handle_view_file: {e}", exc_info=True)
            return False, f"❌ Ошибка при чтении файла: {str(e)}"
            
    async def _handle_create_project(self, context: ContextTypes.DEFAULT_TYPE, **kwargs) -> Tuple[bool, str]:
        """Handle project creation"""
        from core.project.manager import ProjectManager
        from datetime import datetime
        
        # Get the project name from kwargs (can be 'name' or 'project_name')
        name = kwargs.get('name') or kwargs.get('project_name')
        if not name:
            # If no name provided, generate a default one
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            name = f'project_{timestamp}'
            
        # Clean up the name to be filesystem-safe
        import re
        name = re.sub(r'[^\w\-]', '_', name).strip('_').lower()
        if not name:
            name = 'new_project'
            
        project_manager = context.bot_data.get('project_manager')
        if not project_manager:
            return False, "❌ ProjectManager не инициализирован"
            
        try:
            # Create project directory
            project_path = project_manager.get_project_path(name)
            project_path.mkdir(parents=True, exist_ok=True)
            
            # Create project config
            config = {
                'name': name,
                'created_at': str(datetime.now()),
                'description': kwargs.get('description', 'Новый проект')
            }
            
            config_path = project_path / '.project.json'
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
                
            # Update active project
            chat_id = getattr(context, '_chat_id', 0)
            if chat_id is not None:
                active_projects = context.bot_data.setdefault('active_projects', {})
                active_projects[str(chat_id)] = name
                
            return True, f"✅ Проект '{name}' успешно создан в {project_path}"
            
        except Exception as e:
            logger.error(f"Error creating project: {e}", exc_info=True)
            return False, f"❌ Ошибка при создании проекта: {str(e)}"
    
    async def _handle_create_file(self, context: ContextTypes.DEFAULT_TYPE, name: str, content: str = "", **kwargs) -> Tuple[bool, str]:
        """Handle file creation"""
        project_manager = context.bot_data.get('project_manager')
        if not project_manager:
            return False, "❌ ProjectManager не инициализирован"
            
        # Get chat ID (0 for CLI mode)
        chat_id = getattr(context, '_chat_id', 0)
        chat_id_str = str(chat_id)
            
        # Get active project from context or project manager
        active_projects = context.bot_data.get('active_projects', {})
        current_project = active_projects.get(chat_id_str)
        
        # If no active project in context, try to get it from project manager
        if not current_project and project_manager.current_project:
            current_project = project_manager.current_project
            # Update context to keep it in sync
            if 'active_projects' not in context.bot_data:
                context.bot_data['active_projects'] = {}
            context.bot_data['active_projects'][chat_id_str] = current_project
        
        if not current_project:
            return False, "❌ Не выбран активный проект. Сначала создайте или выберите проект."
            
        try:
            # Get project path and create parent directories if needed
            project_path = project_manager.get_project_path(current_project)
            if not project_path or not project_path.exists():
                return False, f"❌ Директория проекта {current_project} не найдена"
                
            file_path = project_path / name
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write file with content
            file_path.write_text(content, encoding='utf-8')
            
            return True, f"✅ Файл {name} успешно создан в проекте {current_project}"
            
        except Exception as e:
            logger.error(f"Error creating file: {e}", exc_info=True)
            return False, f"❌ Ошибка при создании файла: {str(e)}"
    
    async def _handle_list_projects(self, context: ContextTypes.DEFAULT_TYPE, **kwargs) -> Tuple[bool, str]:
        """Handle listing all projects"""
        project_manager = context.bot_data.get('project_manager')
        if not project_manager:
            return False, "❌ ProjectManager не инициализирован"
            
        try:
            # Use the projects_dir attribute directly
            projects_dir = project_manager.projects_dir
            if not projects_dir.exists():
                return True, "ℹ️ Нет созданных проектов"
                
            # List all directories in projects_dir that are valid projects
            projects = []
            for d in projects_dir.iterdir():
                if d.is_dir() and not d.name.startswith('.'):
                    # Check if it's a valid project by looking for config file
                    if (d / '.project.json').exists():
                        projects.append(d.name)
                        
            if not projects:
                return True, "ℹ️ Нет созданных проектов"
                
            projects_list = "\n".join(f"• {name}" for name in sorted(projects))
            return True, f"📋 Список проектов:\n{projects_list}"
            
        except Exception as e:
            logger.error(f"Error listing projects: {e}", exc_info=True)
            return False, f"❌ Ошибка при получении списка проектов: {str(e)}"
    
    async def _handle_switch_project(self, context: ContextTypes.DEFAULT_TYPE, project_name: str = None, **kwargs) -> Tuple[bool, str]:
        """
        Переключиться на указанный проект и обновить все необходимые состояния
        
        Args:
            context: Контекст бота с данными
            project_name: Название проекта для переключения
            
        Returns:
            Tuple[bool, str]: Статус выполнения и сообщение
        """
        try:
            # Получаем менеджер проектов
            project_manager = context.bot_data.get('project_manager')
            if not project_manager:
                logger.error("ProjectManager не найден в контексте")
                return False, "❌ Ошибка: ProjectManager не инициализирован"
                
            # Получаем имя проекта из kwargs, если не указано напрямую
            if not project_name:
                project_name = kwargs.get('project_name') or kwargs.get('name')
                if not project_name:
                    logger.warning("Не указано имя проекта для переключения")
                    return False, "❌ Не указано имя проекта"
            
            logger.info(f"Попытка переключиться на проект: {project_name}")
            
            # Используем метод switch_project из ProjectManager, который сохраняет состояние
            if not project_manager.switch_project(project_name):
                logger.error(f"Не удалось переключиться на проект: {project_name}")
                return False, f"❌ Не удалось переключиться на проект {project_name}. Проверьте название проекта."
            
            # Получаем chat_id (0 для CLI)
            chat_id = getattr(context, '_chat_id', 0)
            chat_id_str = str(chat_id)
            
            # Обновляем активные проекты в контексте
            if 'active_projects' not in context.bot_data:
                context.bot_data['active_projects'] = {}
            context.bot_data['active_projects'][chat_id_str] = project_name
            
            # Обновляем переменную экземпляра
            if not hasattr(self, '_active_projects'):
                self._active_projects = {}
            self._active_projects[chat_id_str] = project_name
            
            logger.info(f"Успешно переключено на проект: {project_name}")
            logger.debug(f"Текущий проект в ProjectManager: {project_manager.current_project}")
            logger.debug(f"Активные проекты в контексте: {context.bot_data['active_projects']}")
            
            return True, f"✅ Успешно переключено на проект: {project_name}"
            
        except Exception as e:
            logger.error(f"Ошибка при переключении проекта: {e}", exc_info=True)
            return False, f"❌ Ошибка при переключении проекта: {str(e)}"
            return False, f"❌ Ошибка при переключении на проект: {str(e)}"
    
    async def _handle_list_files(self, context: ContextTypes.DEFAULT_TYPE, path: str = ".", **kwargs) -> Tuple[bool, str]:
        """List files in project with detailed information"""
        try:
            import os
            from pathlib import Path
            
            project_manager = context.bot_data.get('project_manager')
            if not project_manager:
                return False, "❌ ProjectManager не инициализирован"
            
            # Get chat ID or use default for CLI
            chat_id = getattr(context, '_chat_id', 0)
            chat_id_str = str(chat_id)
            
            # Get active project from context or project manager
            active_projects = context.bot_data.get('active_projects', {})
            current_project = active_projects.get(chat_id_str)
            
            # If no active project in context, try to get it from project manager
            if not current_project and project_manager.current_project:
                current_project = project_manager.current_project
                # Update context to keep it in sync
                if 'active_projects' not in context.bot_data:
                    context.bot_data['active_projects'] = {}
                context.bot_data['active_projects'][chat_id_str] = current_project
            
            if not current_project:
                return False, "❌ Активный проект не выбран. Используйте команду /switch_project или выберите проект."
                
            # Get the project directory path
            project_path = project_manager.get_project_path(current_project)
            if not project_path or not project_path.exists():
                return False, f"❌ Директория проекта {current_project} не найдена"
                
            # Resolve the target path within the project
            target_path = project_path / path
            if not target_path.exists():
                return False, f"❌ Указанный путь не найден: {path}"
                
            # List files and directories
            try:
                items = []
                for item in target_path.iterdir():
                    item_path = target_path / item.name
                    item_type = "📁" if item_path.is_dir() else "📄"
                    item_size = f"{item_path.stat().st_size / 1024:.1f} KB" if item_path.is_file() else ""
                    items.append(f"{item_type} {item.name} {item_size}".strip())
                
                if not items:
                    return True, f"📂 Папка пуста: {path if path != '.' else 'корневая директория'}"
                    
                files_list = "\n".join(sorted(items))
                return True, f"📂 Содержимое {path if path != '.' else 'корневой директории'}:\n{files_list}"
                
            except Exception as e:
                logger.error(f"Ошибка при чтении директории: {e}", exc_info=True)
                return False, f"❌ Ошибка при чтении директории: {str(e)}"
            if not current_project and project_manager.current_project:
                current_project = project_manager.current_project
                active_projects[chat_id_str] = current_project
                context.bot_data['active_projects'] = active_projects
            
            if not current_project:
                return False, "❌ Активный проект не выбран. Сначала переключитесь на проект."
            
            # Build full path
            base_dir = os.path.join("projects", current_project)
            full_path = os.path.normpath(os.path.join(base_dir, path))
            
            # Security check: prevent directory traversal
            if not os.path.abspath(full_path).startswith(os.path.abspath(base_dir)):
                return False, "❌ Ошибка безопасности: недопустимый путь"
            
            # Check if path exists
            if not os.path.exists(full_path):
                return False, f"❌ Путь не найден: {path}"
            
            # Check if it's a directory
            if not os.path.isdir(full_path):
                return False, f"❌ Указанный путь не является директорией: {path}"
            
            # List files with details
            from datetime import datetime
            import stat
            
            files = []
            dirs = []
            
            for item in os.scandir(full_path):
                try:
                    stat_info = item.stat()
                    size = stat_info.st_size
                    mtime = datetime.fromtimestamp(stat_info.st_mtime)
                    
                    # Format size
                    if size < 1024:
                        size_str = f"{size} B"
                    elif size < 1024 * 1024:
                        size_str = f"{size/1024:.1f} KB"
                    else:
                        size_str = f"{size/(1024*1024):.1f} MB"
                    
                    # Format permissions
                    mode = stat_info.st_mode
                    perms = ""
                    for who in "USR", "GRP", "OTH":
                        for what in "R", "W", "X":
                            if mode & getattr(stat, f"S_I{what}{who}"):
                                perms += what.lower()
                            else:
                                perms += "-"
                    
                    entry = {
                        'name': item.name,
                        'is_dir': item.is_dir(),
                        'size': size_str,
                        'mtime': mtime.strftime("%Y-%m-%d %H:%M"),
                        'perms': perms
                    }
                    
                    if item.is_dir():
                        dirs.append(entry)
                    else:
                        files.append(entry)
                        
                except Exception as e:
                    logger.warning(f"Error getting info for {item.name}: {e}")
            
            # Sort directories first, then files, both alphabetically
            dirs.sort(key=lambda x: x['name'].lower())
            files.sort(key=lambda x: x['name'].lower())
            
            # Format output
            output = [f"📂 Содержимое директории: {path} в проекте {current_project}\n"]
            
            # Add parent directory link if not root
            if path != ".":
                parent_dir = os.path.dirname(path)
                if parent_dir == "":
                    parent_dir = "."
                output.append(f"📁 [..] (перейти в родительскую директорию)")
            
            # Add directories
            for d in dirs:
                output.append(
                    f"📁 {d['name']}/\t"
                    f"{d['mtime']}  {d['size']:>8}  {d['perms']}"
                )
            
            # Add files
            for f in files:
                output.append(
                    f"📄 {f['name']}\t"
                    f"{f['mtime']}  {f['size']:>8}  {f['perms']}"
                )
            
            if not dirs and not files:
                output.append("Директория пуста")
            
            return True, "\n".join(output)
            
        except Exception as e:
            logger.error(f"Error listing files: {e}", exc_info=True)
            return False, f"❌ Ошибка при получении списка файлов: {str(e)}"""
    
    async def _handle_view_file(self, context: ContextTypes.DEFAULT_TYPE, **kwargs) -> Tuple[bool, str]:
        """View file contents with enhanced error handling
        
        Args:
            context: Bot context containing project manager and active projects
            **kwargs: Should contain either 'path' or 'file_path' parameter with the file path
            
        Returns:
            Tuple[bool, str]: Success status and detailed message
        """
        try:
            # Get the file path from either 'path' or 'file_path' parameter
            path = kwargs.get('path') or kwargs.get('file_path')
            
            if not path:
                logger.warning("No file path provided in view_file command")
                return False, "❌ Ошибка: Не указан путь к файлу.\n\nПожалуйста, укажите путь к файлу, например:\n`/view_file test.py`"
                
            logger.info(f"Attempting to view file: {path}")
            
            # Get project manager
            project_manager = context.bot_data.get('project_manager')
            if not project_manager:
                error_msg = "ProjectManager не инициализирован. Не удалось получить доступ к менеджеру проектов."
                logger.error(error_msg)
                return False, f"❌ {error_msg}"
                
            # Get active project
            active_projects = context.bot_data.get('active_projects', {})
            chat_id = getattr(context, '_chat_id', 0)
            chat_id_str = str(chat_id)
            
            if not active_projects or chat_id_str not in active_projects:
                error_msg = "Не выбран активный проект."
                logger.warning(f"{error_msg} Chat ID: {chat_id}")
                return False, (
                    "❌ Ошибка: Не выбран активный проект.\n\n"
                    "Сначала создайте или выберите проект, используя команды:\n"
                    "• `/create_project имя_проекта` - создать новый проект\n"
                    "• `/switch_project имя_проекта` - переключиться на существующий проект"
                )
                
            current_project = active_projects[chat_id_str]
            logger.info(f"Current project for chat {chat_id}: {current_project}")
            
            # Get project path
            project_path = project_manager.get_project_path()
            if not project_path or not project_path.exists():
                error_msg = f"Не удалось найти директорию проекта: {project_path}"
                logger.error(error_msg)
                return False, f"❌ {error_msg}"
                
            # Build full file path
            try:
                file_path = (project_path / path).resolve()
                
                # Security check: ensure the file is within the project directory
                if not file_path.is_relative_to(project_path):
                    error_msg = f"Попытка доступа к файлу за пределами проекта: {file_path}"
                    logger.warning(error_msg)
                    return False, f"❌ Ошибка безопасности: {error_msg}"
                    
            except Exception as e:
                error_msg = f"Некорректный путь к файлу: {path}"
                logger.error(f"{error_msg}: {e}", exc_info=True)
                return False, f"❌ {error_msg}. Пожалуйста, проверьте правильность пути."
            
            # Check if file exists and is not a directory
            if not file_path.exists():
                return False, (
                    f"❌ Файл не найден: `{path}`\n\n"
                    "Возможные причины:\n"
                    f"• Файл `{path}` не существует\n"
                    "• Неправильно указан путь\n\n"
                    "Проверьте правильность пути с помощью команды `/list_files`"
                )
                
            if file_path.is_dir():
                return False, (
                    f"❌ Указана директория: `{path}`\n\n"
                    f"Используйте команду `/list_files {path}` для просмотра содержимого директории."
                )
            
            # Read file content
            try:
                content = file_path.read_text(encoding='utf-8')
                file_size = file_path.stat().st_size
                
                # Truncate very large files
                max_size = 100 * 1024  # 100KB
                truncated = False
                if file_size > max_size:
                    content = content[:max_size] + "\n\n[Содержимое обрезано. Файл слишком большой для отображения]"
                    truncated = True
                
                response = [
                    f"📄 *{path}* ({file_size} байт)",
                    "```" + ("python" if path.endswith(".py") else ""),
                    content,
                    "```"
                ]
                
                if truncated:
                    response.append(f"\n_Файл обрезан. Полный размер: {file_size} байт_")
                
                return True, "\n".join(response)
                
            except UnicodeDecodeError:
                return False, (
                    f"❌ Ошибка: Файл `{path}` не является текстовым файлом.\n\n"
                    "Поддерживается только просмотр текстовых файлов."
                )
                
            except Exception as e:
                error_msg = f"Ошибка при чтении файла: {str(e)}"
                logger.error(f"{error_msg} (file: {file_path})", exc_info=True)
                return False, f"❌ {error_msg}"
                
        except Exception as e:
            error_msg = f"Непредвиденная ошибка при обработке запроса: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return False, f"❌ {error_msg}\n\nПожалуйста, попробуйте снова или обратитесь к администратору."
    
    async def _handle_run_code(self, context: ContextTypes.DEFAULT_TYPE, code: str = "", file: str = "", **kwargs) -> Tuple[bool, str]:
        """Run Python code"""
        if not code and not file:
            return False, "❌ Не указан код для выполнения"
            
        if file:
            project_manager = context.bot_data.get('project_manager')
            if not project_manager:
                return False, "❌ ProjectManager не инициализирован"
                
            file_path = project_manager.get_project_path() / file
            if not file_path.exists():
                return False, f"❌ Файл не найден: {file}"
                
            try:
                code = file_path.read_text(encoding='utf-8')
            except Exception as e:
                return False, f"❌ Ошибка при чтении файла: {str(e)}"
        
        # Here you would typically run the code in a safe environment
        # For now, we'll just return the code that would be executed
        return True, f"```python\n# Код для выполнения:\n{code}\n```"
    
    async def _analyze_python_file(self, file_path: Path) -> Dict[str, Any]:
        """Анализирует Python файл и возвращает статистику"""
        try:
            content = file_path.read_text(encoding='utf-8')
            lines = content.splitlines()
            
            # Базовая статистика
            stats = {
                'file': str(file_path.name),
                'lines': len(lines),
                'empty_lines': sum(1 for line in lines if not line.strip()),
                'comment_lines': sum(1 for line in lines if line.strip().startswith('#')),
                'imports': [],
                'functions': [],
                'classes': [],
                'has_docstrings': False,
                'has_tests': any('test' in file_path.name.lower() or 'test_' in file_path.stem.lower() for file_path in [file_path])
            }
            
            # Анализ кода
            in_docstring = False
            in_function = False
            in_class = False
            
            for line in lines:
                line = line.strip()
                
                # Пропускаем пустые строки и комментарии
                if not line or line.startswith('#'):
                    continue
                    
                # Проверяем импорты
                if line.startswith(('import ', 'from ')):
                    stats['imports'].append(line)
                
                # Проверяем классы
                elif line.startswith('class '):
                    stats['classes'].append(line.split('(')[0].replace('class ', '').strip())
                    in_class = True
                
                # Проверяем функции
                elif line.startswith('def '):
                    stats['functions'].append(line.split('(')[0].replace('def ', '').strip())
                    in_function = True
                
                # Проверяем docstrings
                if '"""' in line or "'''" in line:
                    if not in_docstring:
                        stats['has_docstrings'] = True
                    in_docstring = not in_docstring
            
            return stats
            
        except Exception as e:
            logger.error(f"Ошибка при анализе файла {file_path}: {e}")
            return {'error': str(e), 'file': str(file_path.name)}
    
    async def _analyze_project_structure(self, project_path: Path) -> Dict[str, Any]:
        """Анализирует структуру проекта"""
        analysis = {
            'total_files': 0,
            'file_types': {},
            'python_files': [],
            'requirements_files': [],
            'has_requirements': False,
            'has_readme': False,
            'has_license': False,
            'has_git': False,
            'directories': []
        }
        
        try:
            # Сканируем все файлы в проекте
            for item in project_path.rglob('*'):
                if item.is_file():
                    analysis['total_files'] += 1
                    
                    # Анализируем расширение файла
                    ext = item.suffix.lower()
                    analysis['file_types'][ext] = analysis['file_types'].get(ext, 0) + 1
                    
                    # Проверяем специальные файлы
                    if item.name.lower() == 'requirements.txt':
                        analysis['requirements_files'].append(str(item.relative_to(project_path)))
                        analysis['has_requirements'] = True
                    elif item.name.lower() == 'readme.md':
                        analysis['has_readme'] = True
                    elif item.name.lower() in ['license', 'license.txt', 'license.md']:
                        analysis['has_license'] = True
                    elif item.name == '.git' and item.is_dir():
                        analysis['has_git'] = True
                    
                    # Анализируем Python файлы
                    if ext == '.py':
                        analysis['python_files'].append(str(item.relative_to(project_path)))
                
                elif item.is_dir() and item.name not in ['__pycache__', '.git', '.idea', 'venv', 'env']:
                    analysis['directories'].append(str(item.relative_to(project_path)))
            
            return analysis
            
        except Exception as e:
            logger.error(f"Ошибка при анализе структуры проекта: {e}")
            return {'error': str(e)}
    
    async def _generate_analysis_report(self, project_name: str, structure: Dict[str, Any], 
                                     code_stats: List[Dict[str, Any]]) -> str:
        """Генерирует отчет по анализу проекта"""
        # Основная информация
        report = [
            f"# 📊 Анализ проекта: *{project_name}*\n",
            "## 📂 Общая структура проекта"
        ]
        
        # Статистика по файлам
        report.append(f"• Всего файлов: {structure['total_files']}")
        if structure['file_types']:
            report.append("• Распределение по типам файлов:")
            for ext, count in sorted(structure['file_types'].items(), key=lambda x: x[1], reverse=True):
                report.append(f"  - {ext if ext else 'без расширения'}: {count}")
        
        # Python-специфичная статистика
        python_files = [f for f in code_stats if not f.get('error')]
        if python_files:
            total_lines = sum(f['lines'] for f in python_files)
            total_functions = sum(len(f.get('functions', [])) for f in python_files)
            total_classes = sum(len(f.get('classes', [])) for f in python_files)
            
            report.extend([
                "\n## 🐍 Python-код",
                f"• Файлов с кодом: {len(python_files)}",
                f"• Всего строк кода: {total_lines}",
                f"• Функций: {total_functions}",
                f"• Классов: {total_classes}",
                f"• Файлов с тестами: {sum(1 for f in python_files if f.get('has_tests'))}",
                f"• Файлов с документацией: {sum(1 for f in python_files if f.get('has_docstrings'))}"
            ])
        
        # Рекомендации
        recommendations = ["\n## 💡 Рекомендации"]
        
        if not structure['has_readme']:
            recommendations.append("• Добавьте файл README.md с описанием проекта")
        
        if not structure['has_requirements']:
            recommendations.append("• Добавьте файл requirements.txt с зависимостями")
        
        if not structure['has_license']:
            recommendations.append("• Добавьте файл LICENSE с лицензией")
            
        if not any(f.get('has_tests') for f in python_files):
            recommendations.append("• Добавьте тесты для вашего кода")
            
        if recommendations:
            report.extend(recommendations)
        
        return "\n".join(report)
    
    async def _handle_analyze_project(self, context: ContextTypes.DEFAULT_TYPE, **kwargs) -> Tuple[bool, str]:
        """
        Анализирует выбранный проект
        
        Args:
            context: Контекст бота
            **kwargs: Дополнительные параметры
            
        Returns:
            Tuple[bool, str]: Статус выполнения и сообщение с анализом
        """
        try:
            project_manager = context.bot_data.get('project_manager')
            if not project_manager or not project_manager.current_project:
                return False, "❌ Нет активного проекта. Сначала создайте или выберите проект."
                
            project_name = project_manager.current_project
            project_path = project_manager.get_project_path(project_name)
            
            if not project_path or not project_path.exists():
                error_msg = f"Project directory not found: {project_path}"
                logger.error(error_msg)
                return False, f"❌ Директория проекта не найдена: {project_path}"
            
            logger.info(f"Analyzing project: {project_name} at {project_path}")
            
            # Initialize project analyzer
            from core.project.analyzer import ProjectAnalyzer
            analyzer = ProjectAnalyzer(project_path)
            
            # Analyze project
            analysis = analyzer.analyze_project()
            logger.debug(f"Project analysis result: {analysis}")
            
            if 'error' in analysis:
                error_msg = f"Ошибка при анализе проекта: {analysis['error']}"
                logger.error(error_msg)
                return False, f"❌ {error_msg}"
            
            # Format the analysis results
            response = [
                f"📊 *Анализ проекта: {project_name}*\n",
                f"📂 Директория: `{project_path}`"
            ]
            
            # Add statistics if available
            if 'stats' in analysis and analysis['stats']:
                stats = analysis['stats']
                response.extend([
                    "\n*📊 Статистика:*",
                    f"• Всего файлов: {stats.get('total_files', 0)}",
                    f"• Общий размер: {self._format_size(stats.get('total_size', 0))}",
                    f"• Количество директорий: {stats.get('dir_count', 0)}"
                ])
            
            # Add file structure if available
            if 'structure' in analysis and analysis['structure']:
                structure = analysis['structure']
                response.append("\n*📁 Структура проекта:*")
                
                # Helper function to get file description
                def get_file_description(file_name: str) -> str:
                    """Возвращает описание файла на основе его имени и расширения"""
                    file_lower = file_name.lower()
                    
                    if file_name == 'README.md':
                        return " - Документация проекта"
                    elif file_name == 'requirements.txt':
                        return " - Зависимости Python"
                    elif file_name == 'setup.py':
                        return " - Скрипт установки пакета"
                    elif file_name == '.gitignore':
                        return " - Игнорируемые файлы Git"
                    elif file_name == '.env':
                        return " - Переменные окружения"
                    elif file_name.endswith('.py'):
                        if file_name == 'main.py':
                            return " - Главный исполняемый файл"
                        elif file_name.startswith('test_'):
                            return " - Тесты"
                        return " - Python модуль"
                    elif file_name.endswith('.json'):
                        return " - Файл конфигурации JSON"
                    elif file_name.endswith(('.yaml', '.yml')):
                        return " - Файл конфигурации YAML"
                    elif file_name.endswith('.md'):
                        return " - Документация"
                    return ""
                
                # Helper function to get directory description
                def get_directory_description(dir_name: str) -> str:
                    """Возвращает описание директории"""
                    dir_lower = dir_name.lower()
                    
                    if dir_lower in ('src', 'source'):
                        return " - Исходный код приложения"
                    elif dir_lower == 'tests':
                        return " - Тесты"
                    elif dir_lower in ('docs', 'documentation'):
                        return " - Документация"
                    elif dir_lower in ('config', 'conf'):
                        return " - Конфигурационные файлы"
                    elif dir_lower in ('static', 'assets'):
                        return " - Статические файлы (CSS, JS, изображения)"
                    elif dir_lower == 'templates':
                        return " - HTML шаблоны"
                    elif dir_lower == 'migrations':
                        return " - Миграции базы данных"
                    return ""
                
                # Helper function to flatten the tree structure
                def get_structure_items(node, prefix=''):
                    items = []
                    name = node.get('name', '')
                    node_type = node.get('type', '')
                    
                    if node_type == 'file':
                        description = get_file_description(name)
                        items.append(f"{prefix}📄 {name}{description}")
                    elif node_type == 'directory':
                        description = get_directory_description(name)
                        items.append(f"{prefix}📁 {name}/{description}")
                        for child in node.get('children', [])[:5]:  # Show first 5 items per directory
                            items.extend(get_structure_items(child, prefix + '  '))
                        if len(node.get('children', [])) > 5:
                            items.append(f"{prefix}  ... и еще {len(node['children']) - 5} элементов")
                    elif node_type == '...':
                        items.append(f"{prefix}... (глубина ограничена)")
                    return items
                
                # Add the top-level structure items
                structure_items = get_structure_items(structure)
                response.extend(structure_items[:15])  # Show first 15 items total
                if len(structure_items) > 15:
                    response.append("... и еще элементов (используйте /list_files для полного списка)")
            
            # Add project summary if available
            if 'summary' in analysis and analysis['summary']:
                summary = analysis['summary']
                response.extend([
                    "\n*🔍 Анализ проекта:*",
                    f"• *Тип проекта:* {summary.get('project_type', 'Не определен')}",
                    f"• *Дата создания:* {summary.get('created_date', 'Неизвестно')}",
                    f"• *Последнее изменение:* {summary.get('modified_date', 'Неизвестно')}",
                    f"• *Уровень зрелости:* {summary.get('maturity', {}).get('level', 'Неизвестно')} ({summary.get('maturity', {}).get('score', 0)}/{summary.get('maturity', {}).get('max_score', 10)})",
                    f"• *Описание:* {summary.get('maturity', {}).get('description', 'Нет описания')}",
                    "\n*📌 Рекомендации по развитию:*"
                ])
                
                # Add recommendations or a message if none
                recommendations = summary.get('recommendations', [])
                if recommendations:
                    for i, rec in enumerate(recommendations, 1):
                        response.append(f"{i}. {rec}")
                else:
                    response.append("Отличная работа! Проект выглядит хорошо структурированным.")
            
            return True, '\n'.join(response)
            
        except Exception as e:
            error_msg = f"Непредвиденная ошибка: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return False, f"❌ {error_msg}\n\nПожалуйста, попробуйте снова или обратитесь к администратору."
    
    def _format_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"
    
    async def _handle_analyze_code(self, context: ContextTypes.DEFAULT_TYPE, code: str = "", file: str = "", **kwargs) -> Tuple[bool, str]:
        """Анализирует код из строки или файла"""
        if not code and not file:
            return False, "❌ Не указан код для анализа"
            
        if file:
            project_manager = context.bot_data.get('project_manager')
            if not project_manager:
                return False, "❌ ProjectManager не инициализирован"
                
            file_path = project_manager.get_project_path() / file
            if not file_path.exists():
                return False, f"❌ Файл не найден: {file}"
                
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    code = f.read()
            except Exception as e:
                return False, f"❌ Ошибка при чтении файла: {str(e)}"
        
        # Simple code analysis
        lines = code.count('\n') + 1
        chars = len(code)
        
        analysis = f"""🔍 Анализ кода:
• Строк кода: {lines}
• Символов: {chars}
• Примерный уровень сложности: {'Низкий' if lines < 50 else 'Средний' if lines < 200 else 'Высокий'}

Рекомендации:
{'Код выглядит хорошо структурированным.' if lines < 100 else 'Рассмотрите возможность разделения на модули.'}
{'Добавьте документацию к функциям и классам.' if 'def ' in code or 'class ' in code and '"""' not in code else ''}
"""
        
        return True, analysis

# Global instance
nlp_processor = NLPProcessor()
