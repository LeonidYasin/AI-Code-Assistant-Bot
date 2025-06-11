"""Command processing module for the bot."""
import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional, Union

from telegram import Update, User, Chat, Bot, Message
from telegram.ext import ContextTypes, CallbackContext

logger = logging.getLogger(__name__)

# Path to store the project state
STATE_FILE = Path("bot_state.json")

class CommandProcessor:
    """Handles command processing for the bot."""
    
    _instance = None
    _initialized = False
    
    def __new__(cls, app=None):
        if cls._instance is None:
            cls._instance = super(CommandProcessor, cls).__new__(cls)
        return cls._instance
    
    def __init__(self, app=None):
        """Initialize with the bot application instance."""
        if not self._initialized and app is not None:
            self.app = app
            self._project_handlers = None
            # Initialize state
            self._active_projects = {}
            self._project_states = {}
            # Load saved state
            self._load_state()
            self._initialized = True
    
    def _load_state(self) -> None:
        """Load project state from file."""
        if STATE_FILE.exists():
            try:
                with open(STATE_FILE, 'r', encoding='utf-8') as f:
                    state = json.load(f)
                    self._active_projects = state.get('active_projects', {})
                    self._project_states = state.get('project_states', {})
                    # Convert string keys back to integers for chat IDs
                    self._active_projects = {int(k): v for k, v in self._active_projects.items()}
                    self._project_states = {int(k): v for k, v in self._project_states.items()}
            except Exception as e:
                logger.error(f"Failed to load state: {e}")
    
    def _save_state(self) -> None:
        """Save project state to file."""
        try:
            # Convert int keys to strings for JSON serialization
            state = {
                'active_projects': {str(k): v for k, v in self._active_projects.items()},
                'project_states': {str(k): v for k, v in self._project_states.items()}
            }
            with open(STATE_FILE, 'w', encoding='utf-8') as f:
                json.dump(state, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Failed to save state: {e}")
    
    def get_commands(self) -> dict:
        """
        Get a dictionary of all registered commands and their descriptions.
        
        Returns:
            dict: Dictionary mapping command names to their descriptions
        """
        commands = {}
        
        # Get commands from the application's handlers
        if hasattr(self, 'app') and hasattr(self.app, 'handlers'):
            for handler in self.app.handlers.get(0, []):  # Group 0 is for commands
                if hasattr(handler, 'commands'):
                    for cmd in handler.commands:
                        # Get the callback function's docstring as description
                        desc = getattr(handler.callback, '__doc__', 'No description available')
                        if desc:
                            # Use first line of docstring as description
                            desc = desc.strip().split('\n')[0]
                        commands[f'/{cmd}'] = desc or 'No description available'
        
        # Add default commands if none found
        if not commands:
            commands = {
                '/start': 'Начать работу с ботом',
                '/help': 'Показать справку',
                '/project': 'Управление проектами',
                '/analyze': 'Анализ кода',
                '/analyze_project': 'Анализ проекта'
            }
            
        return commands
            
    def _create_fake_update(self, command_text: str, chat_id: int):
        """Create a fake update object for CLI commands."""
        from telegram import Chat, User, Message as TelegramMessage
        
        # Create a user object
        user = User(
            id=chat_id,
            first_name='CLI',
            is_bot=False,
            username='cli_user',
        )
        
        # Create a chat object
        chat = Chat(id=chat_id, type='private')
        
        # Create a message object with all required attributes
        class FakeMessage(TelegramMessage):
            def __init__(self, text, chat, from_user):
                super().__init__(
                    message_id=1,
                    date=None,
                    chat=chat,
                    from_user=from_user,
                    text=text
                )
                self._unfreeze()
                # chat_id is a property in the parent class that uses chat.id
                # so we don't need to set it directly
                self.from_user = from_user
                self.effective_chat = chat
                self.effective_user = from_user
                # Store the bot instance for reply methods
                self._bot = None
            
            @property
            def bot(self):
                return self._bot
                
            @bot.setter
            def bot(self, value):
                self._bot = value
            
            def get_bot(self):
                return self._bot
            
            async def reply_text(self, text, **kwargs):
                print("\n" + "="*50)
                print("BOT RESPONSE:")
                print("-"*50)
                print(text)
                if kwargs.get('parse_mode') == 'HTML':
                    print("\n(HTML content rendered as plain text)")
                print("="*50 + "\n")
                return type('Message', (), {'message_id': 1})
        
        # Create update object with required attributes
        class FakeUpdate:
            def __init__(self, text, chat_id, user, chat):
                self.message = FakeMessage(text, chat, user)
                self.effective_message = self.message
                self.effective_chat = chat
                self.effective_user = user
        
        return FakeUpdate(command_text, chat_id, user, chat)
    
    def _create_fake_context(self):
        """Create a fake context object for CLI commands."""
        from telegram.ext import CallbackContext
        
        class FakeContext(CallbackContext):
            def __init__(self):
                # Create a simple application reference for the context
                app = type('FakeApp', (), {'bot': type('FakeBot', (), {'data': {}})})
                super().__init__(application=app)
                self._bot_data = {}
                self._chat_data = {}
                self._user_data = {}
            
            @property
            def bot_data(self):
                return self._bot_data
            
            @bot_data.setter
            def bot_data(self, value):
                self._bot_data = value
            
            @property
            def chat_data(self):
                return self._chat_data
            
            @property
            def user_data(self):
                return self._user_data
            
            async def bot(self):
                # Return a simple bot object with a send_message method
                class FakeBot:
                    async def send_message(self, chat_id, text, **kwargs):
                        print("\n" + "="*50)
                        print("BOT RESPONSE:")
                        print("-"*50)
                        print(text)
                        print("="*50 + "\n")
                        return type('Message', (), {'message_id': 1})
                return FakeBot()
        
        return FakeContext()
    
    async def process_command(self, command_text: str, context=None, chat_id: int = None) -> tuple[bool, str]:
        """Process a command or natural language input from the user.
        
        Args:
            command_text: The full command text or natural language input
            context: The context object (may be None in some cases)
            chat_id: The chat ID to send responses to. If None, runs in CLI mode.
            
        Returns:
            Tuple of (success: bool, response: str)
        """
        if not command_text:
            return False, "❌ Пустая команда"
            
        # Debug information
        print("\n" + "="*50)
        print(f"[DEBUG] process_command")
        print(f"Input: {command_text}")
        print(f"Chat ID: {chat_id}")
        print(f"CLI mode: {chat_id is None}")
        print("Available commands:", ", ".join(f"{k}" for k in (self.app._commands.keys() if hasattr(self.app, '_commands') else [])))
        print("="*50 + "\n")
        
        # If context is provided, use it to get/set bot_data and chat_id
        if context is not None:
            if not hasattr(self, 'bot') and hasattr(context, 'bot_data'):
                self.bot = type('Bot', (), {'bot_data': context.bot_data})  # Minimal bot object
                
            if chat_id is None and hasattr(context, '_chat_id'):
                chat_id = context._chat_id
        
        # Check if we have a command (starts with /)
        if not command_text.startswith('/'):
            # Not a command, forward to NLP processor
            try:
                from handlers.nlp_processor import nlp_processor
                
                print("\n[DEBUG] Processing as natural language input")
                
                # Create or reuse context for CLI mode
                if context is None:
                    class FakeContext:
                        def __init__(self, chat_id):
                            self._chat_id = chat_id or 0
                            self._bot_data = {
                                'active_projects': {},
                                'project_states': {}
                            }
                            # Initialize active_projects if it doesn't exist
                            if str(self._chat_id) not in self._bot_data['active_projects']:
                                self._bot_data['active_projects'][str(self._chat_id)] = None
                            
                        @property
                        def bot_data(self):
                            return self._bot_data
                            
                        @bot_data.setter
                        def bot_data(self, value):
                            self._bot_data = value
                            
                        async def send_message(self, chat_id, text, **kwargs):
                            print("\n" + "="*50)
                            print(f"BOT RESPONSE (NLP):")
                            print("-"*50)
                            print(text)
                            print("="*50 + "\n")
                            return text
                    
                    # Create or reuse context for CLI mode
                    if not hasattr(self, '_cli_context'):
                        self._cli_context = FakeContext(chat_id)
                    context = self._cli_context
                
                # Process the natural language command
                success, response = await nlp_processor.process_command(command_text, context)
                return success, response
                
            except Exception as e:
                import traceback
                error_msg = f"❌ Ошибка при обработке запроса: {str(e)}"
                print(f"Error in NLP processing: {e}")
                traceback.print_exc()
                return False, error_msg
            
        # Remove leading slash and split into command and arguments
        parts = command_text[1:].split()
        if not parts:
            return False, "❌ Не указана команда"
            
        command = parts[0].lower()
        cli_mode = chat_id is None
        effective_chat_id = chat_id or 0  # Use 0 as default chat_id for CLI mode
        
        # Special handling for project commands
        if command == 'project':
            # Check if we have a subcommand
            if len(parts) > 1:
                subcommand = parts[1].strip()
                if subcommand.lower() == 'list':
                    # Special handling for project list command
                    command_text = "/project list"
        
        # Initialize bot_data if not present
        if context is not None and not hasattr(context, 'bot_data'):
            context.bot_data = {}
            
        # Initialize active_projects if not present
        if 'active_projects' not in context.bot_data:
            context.bot_data['active_projects'] = {}
            
        # Make sure we have active_projects in the instance as well
        if not hasattr(self, '_active_projects'):
            self._active_projects = context.bot_data['active_projects']
            
        # Special case for help command
        if command == 'help':
            # Check if it's a specific help request like /help project
            if len(parts) > 1 and parts[1].lower() == 'project':
                help_text = (
                    "🤖 <b>Управление проектами</b>\n\n"
                    "<b>Доступные команды:</b>\n"
                    "• /project list - 📋 Показать список всех проектов\n"
                    "• /project create &lt;имя&gt; - 🆕 Создать новый проект\n"
                    "• /project switch &lt;имя&gt; - 🔄 Переключиться на другой проект\n"
                    "• /project info - ℹ️ Показать информацию о текущем проекте\n\n"
                    "<b>Примеры использования:</b>\n"
                    "• Создать проект: <code>/project create мой_проект</code>\n"
                    "• Переключиться на проект: <code>/project switch мой_проект</code>\n"
                    "• Показать информацию: <code>/project info</code>"
                )
            else:
                # Full rich help text in Russian
                help_text = (
                    "🤖 <b>AI Code Assistant - Помощник разработчика</b>\n\n"
                    "Я помогу вам разрабатывать проекты, используя как команды, так и обычный язык.\n\n"
                    
                    "<b>📂 Работа с проектами</b>\n"
                    "Все проекты хранятся в папке projects/. Вы можете управлять ими командами:\n"
                    "• <code>/project create мой_проект</code> - Создать новый проект\n"
                    "• <code>/project switch мой_проект</code> - Переключиться на проект\n"
                    "• <code>/project list</code> - Список проектов\n"
                    "• <code>/project info</code> - Информация о проекте\n\n"
                    
                    "<b>💬 Естественный язык</b>\n"
                    "Просто напишите, что вы хотите сделать, например:\n"
                    "• <i>Создай новый проект для веб-приложения</i>\n"
                    "• <i>Добавь новый файл main.py с веб-сервером на Flask</i>\n"
                    "• <i>Проанализируй код в файле app.py</i>\n\n"
                    
                    "<b>🚀 Основные команды:</b>\n"
                    "• <code>/start</code> - Начать работу с ботом\n"
                    "• <code>/help</code> - Показать это сообщение\n"
                    "• <code>/analyze &lt;код&gt;</code> - Анализ кода\n"
                    "• <code>/run &lt;файл.py&gt;</code> - Запустить скрипт\n\n"
                    
                    "<b>📝 Примеры запросов:</b>\n"
                    "• <code>Создай REST API на FastAPI</code>\n"
                    "• <code>Добавь обработку ошибок в функцию main()</code>\n"
                    "• <code>Напиши тесты для модуля user.py</code>\n"
                    "• <code>Объясни, как работает этот код</code>\n\n"
                    
                    "<b>🔧 Управление файлами:</b>\n"
                    "• <code>/list [путь]</code> - Показать файлы\n"
                    "• <code>/view &lt;файл&gt;</code> - Просмотреть файл\n"
                    "• <code>/edit &lt;файл&gt;</code> - Редактировать файл\n"
                    "• <code>cmd: &lt;команда&gt;</code> - Выполнить команду\n\n"
                    
                    "<b>⚠️ Безопасность:</b>\n"
                    "• Код выполняется в изолированной среде\n"
                    "• Опасные команды заблокированы\n"
                    "• Доступны только файлы внутри папки проекта"
                )
            
            print("\n" + "="*50)
            print("BOT RESPONSE:")
            print("-"*50)
            print(help_text)
            print("\n(HTML content rendered as plain text)")
            print("="*50 + "\n")
            return True, help_text
            
        # Find and execute the command
        if command in self.app._commands:
            try:
                # For CLI mode, we need to simulate the update and context
                if cli_mode or context is None:
                    # Create a minimal context for CLI mode
                    class CLIContext:
                        def __init__(self, chat_id):
                            self._chat_id = chat_id
                            self.bot_data = context.bot_data if context and hasattr(context, 'bot_data') else {}
                            
                            # Ensure required structures exist
                            if 'active_projects' not in self.bot_data:
                                self.bot_data['active_projects'] = {}
                            if 'project_states' not in self.bot_data:
                                self.bot_data['project_states'] = {}
                                
                            # Sync with instance variables
                            self._active_projects = self.bot_data['active_projects']
                            self._project_states = self.bot_data['project_states']
                            
                            # Store chat_id in bot_data for persistence
                            self.bot_data.setdefault('chat_id', chat_id)
                        
                        async def send_message(self, chat_id, text, parse_mode=None, **kwargs):
                            print(f"\n[CLI MESSAGE] {text}\n")
                            
                        async def reply_text(self, text, parse_mode=None, **kwargs):
                            print(f"\n[CLI MESSAGE] {text}\n")
                            
                        def __getattr__(self, name):
                            # Return None for any other attribute access to avoid AttributeError
                            return None
                    
                    cli_context = CLIContext(effective_chat_id)
                    
                    # Execute the command with the CLI context
                    await self._execute_command(command, command_text, effective_chat_id, cli_mode, cli_context)
                    
                    # Debug: Print state after command processing
                    print("\n[DEBUG] After command processing:")
                    print(f"Active projects: {self._active_projects}")
                    print(f"Project states: {self._project_states}")
                    
                    # Return success with a generic message if no specific response was returned
                    return True, f"✅ Команда '{command}' выполнена успешно"
                else:
                    # In bot mode, just execute normally
                    await self._execute_command(command, command_text, effective_chat_id, cli_mode, context)
                    return True, None  # Response will be sent by the command handler
                
            except Exception as e:
                error_msg = f"❌ Ошибка при выполнении команды '{command}': {str(e)}"
                logger.error(error_msg, exc_info=True)
                
                if cli_mode:
                    return False, error_msg
                else:
                    await context.reply_text(error_msg, parse_mode='Markdown')
                    return False, error_msg
        else:
            error_msg = f"❌ Неизвестная команда: /{command}. Используйте /help для справки."
            if cli_mode:
                return False, error_msg
            else:
                await context.reply_text(error_msg, parse_mode='Markdown')
                return False, error_msg
    
    async def _ensure_project_handlers(self) -> None:
        """Ensure project handlers are registered."""
        if self._project_handlers is None:
            try:
                from handlers.project_handlers import register_project_handlers
                from core.llm.client import llm_client
                self._project_handlers = await register_project_handlers(self.app, llm_client)
                logger.info("Project handlers registered successfully")
            except Exception as e:
                logger.error(f"Failed to register project handlers: {e}", exc_info=True)
                self._project_handlers = None
    
    async def _execute_command(self, command: str, command_text: str, chat_id: int, cli_mode: bool, context=None) -> None:
        """Execute a command with proper context.
        
        Args:
            command: The command name to execute
            command_text: The full command text
            chat_id: The chat ID to execute the command for
            cli_mode: Whether we're in CLI mode
            
        Returns:
            None - Command handlers are responsible for sending their own responses
        """
        from telegram import Update as TelegramUpdate
        
        # Debug output
        print("\n" + "="*50)
        print("[DEBUG] _execute_command")
        print(f"Command: {command}")
        print(f"Command text: {command_text}")
        print(f"Chat ID: {chat_id}")
        print(f"CLI mode: {cli_mode}")
        print(f"Available commands: {list(self.app._commands.keys())}")
        print("="*50 + "\n")
        
        # Create chat and user objects
        chat = Chat(id=chat_id, type='private')
        user = User(id=chat_id, first_name='CLI User' if cli_mode else 'User', is_bot=False)
        
        # Initialize chat state if it doesn't exist
        if chat_id not in self._active_projects:
            self._active_projects[chat_id] = None
        if chat_id not in self._project_states:
            self._project_states[chat_id] = {}
            
        # Create context data with current state
        context_bot_data = {
            'active_project': {chat_id: self._active_projects[chat_id]},
            'project_states': {chat_id: self._project_states[chat_id].copy()}
        }
        
        if hasattr(self, 'app') and hasattr(self.app, 'bot_data'):
            context_bot_data.update(self.app.bot_data)
        
        # Debug: Print the command handler
        if command in self.app._commands:
            print(f"Found command handler: {self.app._commands[command]}")
        else:
            print(f"No handler found for command: {command}")
        
        # Create message with custom reply_text for CLI mode
        class CLIMessage(Message):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self._bot = None
                self._text = command_text
                self.chat = chat
                self.from_user = user
                
            async def reply_text(self, text, **kwargs):
                print("\n[CLI RESPONSE]" + "="*40)
                print(text)
                print("="*48 + "\n")
                return self
                
            @property
            def text(self):
                return self._text
                
            @text.setter
            def text(self, value):
                self._text = value
        
        # Create a minimal Update object
        message = CLIMessage(
            message_id=0,
            date=None,
            chat=chat,
            text=command_text,
            from_user=user
        )
        
        # Set bot instance if available
        if hasattr(self.app, 'bot'):
            message._bot = self.app.bot
        
        # Create update and context
        update = TelegramUpdate(update_id=0, message=message)
        
        # Create a custom context class to handle our needs
        class CustomContext(CallbackContext):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self._bot_data = context_bot_data
                self._chat_data = {}
                self._user_data = {}
                self.command_processor = self
                self.active_project = context_bot_data.get('active_project', {})
            
            @property
            def bot_data(self):
                return self._bot_data
                
            @bot_data.setter
            def bot_data(self, value):
                self._bot_data = value
            
            @property
            def chat_data(self):
                return self._chat_data
                
            @property
            def user_data(self):
                return self._user_data
        
        # Initialize the context
        context = CustomContext.from_update(update, self.app)
        
        # Debug output
        print("\n[DEBUG] Context initialized with bot_data:")
        print(f"Active projects: {context_bot_data.get('active_project', {})}")
        print(f"Project states: {context_bot_data.get('project_states', {})}")
        
        # Execute the command
        try:
            # Save the current state before executing the command
            prev_active_project = self._active_projects.get(chat_id)
            
            # Execute the command
            await self.app._commands[command](update, context)
            
            # After command execution, update our internal state with any changes
            if hasattr(context, 'active_project') and chat_id in context.active_project:
                new_active_project = context.active_project[chat_id]
                if new_active_project != prev_active_project:
                    self._active_projects[chat_id] = new_active_project
                    print(f"\n[DEBUG] Updated active project for chat {chat_id} to: {new_active_project}")
            
            # Also sync back any changes from bot_data
            if hasattr(context, 'bot_data') and context.bot_data:
                if 'active_project' in context.bot_data and chat_id in context.bot_data['active_project']:
                    self._active_projects[chat_id] = context.bot_data['active_project'][chat_id]
            
            # Save state after each command
            self._save_state()
            
        except Exception as e:
            error_msg = f"❌ Ошибка при выполнении команды: {str(e)}"
            logger.error(f"Error processing command '{command_text}': {e}", exc_info=True)
            
            # Debug: Print current state after error
            print("\n[DEBUG] After error:")
            print(f"app.bot_data.active_project: {getattr(self.app, 'bot_data', {}).get('active_project', 'N/A')}")
            if hasattr(context, 'active_project'):
                print(f"context.active_project: {getattr(context, 'active_project', 'N/A')}")
            
            # Re-raise the exception to be handled by the caller
            raise
    
    async def _send_response(self, chat_id: int, text: str) -> None:
        """Send a response to the specified chat or print to console."""
        if chat_id is None:
            # In CLI mode, just print to console
            print("\n[CLI RESPONSE]" + "="*40)
            print(text)
            print("="*50 + "\n")
        else:
            # In bot mode, send the message
            try:
                await self.app.bot.send_message(chat_id=chat_id, text=text)
            except Exception as e:
                logger.error(f"Failed to send message to chat {chat_id}: {e}")
                print(f"\n[ERROR] Failed to send message to chat {chat_id}:")
                print(text)
                print()
