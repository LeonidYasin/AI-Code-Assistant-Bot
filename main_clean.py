#!/usr/bin/env python3
"""
Main entry point for the AI Code Assistant bot.

This module initializes the bot and sets up all command handlers.
"""
import asyncio
import json
import logging
import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = str(Path(__file__).parent.absolute())
sys.path.insert(0, project_root)

# Set up console encoding first
from core.utils.encoding_utils import setup_console_encoding, configure_logging, safe_print
setup_console_encoding()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Apply safe logging configuration
configure_logging()

# Import core bot components
from core.bot.application import BotApplication

# Import and register modules
from handlers import register_handlers

def get_help_text() -> str:
    """Get the help text for the CLI."""
    return """
🤖 AI Code Assistant - Помощник разработчика

Я помогу вам разрабатывать проекты, используя как команды, так и обычный язык.

📂 Работа с проектами
Все проекты хранятся в папке projects/. Вы можете управлять ими командами:
• /list_projects - Показать список проектов
• /create_project name=имя - Создать новый проект
• /switch_project name=имя - Переключиться на проект
• /project_info - Информация о проекте
• /list_files - Список файлов в проекте

📝 Работа с файлами:
• /view_file path=путь - Просмотреть файл
• /create_file path=путь [content=текст] - Создать файл
• /run_script path=путь - Выполнить скрипт

🤖 Анализ кода:
• /analyze_code path=путь - Анализ файла
• /analyze_project - Анализ всего проекта

🔧 Другие команды:
• /run_code code=код - Выполнить код
• /run_code file=путь - Выполнить код из файла

ℹ️ Справка:
  -h, --help    Показать это сообщение
  -v, --version Показать версию
"""

def show_cli_help():
    """Display CLI help information"""
    print(get_help_text())

class CLIContext:
    """Simple context class for CLI mode."""
    def __init__(self):
        self.bot_data = {}
        self._chat_id = 0
        self.args = []

    @property
    def chat_id(self):
        return self._chat_id

def is_direct_command(command: str) -> bool:
    """Check if the command is a direct command (starts with /)."""
    return command.startswith('/')

async def _process_direct_command(command: str, bot) -> int:
    """Process a direct CLI command (starts with /)."""
    # Remove leading slash and split into parts
    command_parts = command[1:].split()
    if not command_parts:
        print("❌ Не указана команда после слэша")
        return 1
        
    command_name = command_parts[0].lower()
    params = {}
    
    # Parse parameters from command line arguments
    for arg in command_parts[1:]:
        if '=' in arg:
            key, value = arg.split('=', 1)
            # Try to convert value to appropriate type
            if value.lower() == 'true':
                value = True
            elif value.lower() == 'false':
                value = False
            elif value.isdigit():
                value = int(value)
            elif value.replace('.', '', 1).isdigit() and value.count('.') < 2:
                value = float(value)
            params[key] = value
        else:
            # For simple flags without values, assume boolean True
            params[arg] = True
    
    # Get project manager for direct command execution
    project_manager = bot.project_manager
    chat_id = 0  # Use 0 for CLI commands
    
    try:
        # Map commands to their handlers
        if command_name == 'list_projects':
            success, result = project_manager.list_projects()
            if success:
                response = ["📋 Список проектов:"]
                for i, project in enumerate(result, 1):
                    status = "✅" if project.get('has_config', False) else "⚠️"
                    config_status = "" if project.get('has_config', False) else " (без конфигурации)"
                    response.append(
                        f"{i}. {status} {project['name']}{config_status}\n"
                        f"   📁 {project['path']}"
                    )
                print("\n" + "\n".join(response))
            else:
                print(f"❌ Ошибка: {result}")
            return 0 if success else 1
            
        elif command_name == 'create_project':
            if 'name' not in params:
                print("❌ Для команды create_project требуется параметр name")
                return 1
                
            success, result = project_manager.create_project(params['name'])
            if success:
                print(f"✅ Проект '{params['name']}' успешно создан")
                print(f"📁 Путь: {result}")
            else:
                print(f"❌ Ошибка при создании проекта: {result}")
            return 0 if success else 1
            
        elif command_name == 'switch_project':
            if 'name' not in params:
                print("❌ Для команды switch_project требуется параметр name")
                return 1
                
            success, result = project_manager.switch_project(params['name'])
            if success:
                print(f"✅ Переключен на проект: {params['name']}")
            else:
                print(f"❌ Ошибка при переключении проекта: {result}")
            return 0 if success else 1
            
        elif command_name == 'project_info':
            success, result = project_manager.get_project_info()
            if success:
                print("📊 Информация о проекте:")
                print(f"Название: {result.get('name', 'Неизвестно')}")
                print(f"Путь: {result.get('path', 'Неизвестен')}")
                print(f"Дата создания: {result.get('created_at', 'Неизвестна')}")
                print(f"Размер: {result.get('size', '0')}")
                print(f"Количество файлов: {result.get('file_count', 0)}")
            else:
                print(f"❌ Ошибка при получении информации о проекте: {result}")
            return 0 if success else 1
            
        elif command_name == 'list_files':
            path = params.get('path', '.')
            success, result = project_manager.list_files(path)
            if success:
                if not result:
                    print("ℹ️ В проекте нет файлов")
                    return 0
                    
                print(f"📂 Список файлов в проекте ({path}):")
                for file in result:
                    print(f"- {file}")
            else:
                print(f"❌ Ошибка при получении списка файлов: {result}")
            return 0 if success else 1
            
        elif command_name == 'view_file':
            if 'path' not in params:
                print("❌ Для команды view_file требуется параметр path")
                return 1
                
            success, result = project_manager.view_file(params['path'])
            if success:
                print(f"📄 Содержимое файла {params['path']}:")
                print("-" * 50)
                print(result)
                print("-" * 50)
            else:
                print(f"❌ Ошибка при чтении файла: {result}")
            return 0 if success else 1
            
        elif command_name == 'create_file':
            if 'path' not in params:
                print("❌ Для команды create_file требуется параметр path")
                return 1
                
            content = params.get('content', '')
            success, result = project_manager.create_file(params['path'], content)
            if success:
                print(f"✅ Файл успешно создан: {params['path']}")
            else:
                print(f"❌ Ошибка при создании файла: {result}")
            return 0 if success else 1
            
        elif command_name == 'run_script':
            if 'path' not in params:
                print("❌ Для команды run_script требуется параметр path")
                return 1
                
            success, result = project_manager.run_script(params['path'])
            if success:
                print(f"✅ Скрипт выполнен успешно:")
                print(result)
            else:
                print(f"❌ Ошибка при выполнении скрипта: {result}")
            return 0 if success else 1
            
        elif command_name == 'run_code':
            if 'code' not in params and 'file' not in params:
                print("❌ Для команды run_code требуется параметр code или file")
                return 1
                
            if 'file' in params:
                print(f"🔧 Выполнение кода из файла: {params['file']}")
                success, result = project_manager.run_script(params['file'])
            else:
                print("🔧 Выполнение введенного кода...")
                success, result = project_manager.execute_code(params['code'])
                
            if success:
                print("✅ Код выполнен успешно:")
                print(result)
            else:
                print(f"❌ Ошибка при выполнении кода: {result}")
            return 0 if success else 1
            
        elif command_name == 'analyze_code':
            if 'path' not in params:
                print("❌ Для команды analyze_code требуется параметр path")
                return 1
                
            print("🔍 Подготовка к анализу кода...")
            try:
                # Get the file content first
                success, file_content = project_manager.view_file(params['path'])
                if not success:
                    print(f"❌ Не удалось прочитать файл: {file_content}")
                    return 1
                
                print("🤖 Отправка запроса на анализ в ИИ...")
                # Use the project AI for analysis
                project_ai = bot.get_project_ai(chat_id)
                success, result = await project_ai.analyze_code(params['path'])
                
                if success:
                    print("\n✅ Результаты анализа кода:")
                    print("="*50)
                    print(result)
                    print("="*50)
                else:
                    print(f"❌ Ошибка при анализе кода: {result}")
                return 0 if success else 1
                
            except Exception as e:
                print(f"❌ Непредвиденная ошибка при анализе кода: {str(e)}")
                import traceback
                traceback.print_exc()
                return 1
            
        elif command_name == 'analyze_project':
            print("🔍 Подготовка к анализу проекта...")
            try:
                # Get project info first
                success, project_info = project_manager.get_project_info()
                if not success:
                    print(f"❌ Не удалось получить информацию о проекте: {project_info}")
                    return 1
                
                print(f"📊 Анализ проекта: {project_info.get('name', 'Безымянный проект')}")
                print(f"📁 Путь: {project_info.get('path', 'Неизвестен')}")
                print("🤖 Отправка запроса на анализ в ИИ...")
                
                # Use the project AI for analysis
                project_ai = bot.get_project_ai(chat_id)
                success, result = await project_ai.analyze_project()
                
                if success:
                    print("\n✅ Результаты анализа проекта:")
                    print("="*50)
                    print(result)
                    print("="*50)
                else:
                    print(f"❌ Ошибка при анализе проекта: {result}")
                return 0 if success else 1
                
            except Exception as e:
                print(f"❌ Непредвиденная ошибка при анализе проекта: {str(e)}")
                import traceback
                traceback.print_exc()
                return 1
            
        else:
            print("❌ Неизвестная команда. Доступные команды:")
            print("  /list_projects - Показать список проектов")
            print("  /create_project name=имя - Создать новый проект")
            print("  /switch_project name=имя - Переключиться на проект")
            print("  /project_info - Показать информацию о текущем проекте")
            print("  /list_files [path=путь] - Показать файлы в проекте")
            print("  /view_file path=путь - Просмотреть содержимое файла")
            print("  /create_file path=путь [content=текст] - Создать файл")
            print("  /run_script path=путь - Выполнить скрипт")
            print("  /run_code code=код - Выполнить код")
            print("  /run_code file=путь - Выполнить код из файла")
            print("  /analyze_code path=путь - Проанализировать код")
            print("  /analyze_project - Проанализировать весь проект")
            return 1
            
    except Exception as e:
        print(f"❌ Ошибка при выполнении команды: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

async def process_cli_command(bot) -> int:
    """Process the CLI command."""
    if len(sys.argv) < 2:
        show_cli_help()
        return 0
        
    command = sys.argv[1]
    
    # Handle help command
    if command.lower() in ('help', '--help', '-h'):
        show_cli_help()
        return 0
        
    # Handle version command
    if command.lower() in ('--version', '-v'):
        from core import __version__
        print(f"AI Code Assistant v{__version__}")
        return 0
        
    # Handle direct commands (those starting with /)
    if is_direct_command(command):
        return await _process_direct_command(command, bot)
        
    # For non-direct commands, proceed with normal processing
    return await _process_non_direct_command(bot, command)

async def _process_non_direct_command(bot, command: str) -> int:
    """Process non-direct CLI commands (legacy format)."""
    print(f"Обработка команды: {command}")
    # Add your non-direct command processing logic here
    return 0

async def run_cli() -> int:
    """Run the bot in CLI mode."""
    try:
        # Initialize the bot
        bot = BotApplication()
        
        # Initialize project manager if needed
        if not hasattr(bot, 'project_manager'):
            from core.project.manager import ProjectManager
            # Use the bot's base directory as the base path
            base_dir = Path(__file__).parent.absolute()
            bot.project_manager = ProjectManager(base_dir)
            
            # Set a default project for CLI mode
            default_project = 'default_cli_project'
            bot.project_manager.current_project = default_project
            
            # Create projects directory if it doesn't exist
            projects_dir = base_dir / 'projects'
            projects_dir.mkdir(exist_ok=True, parents=True)
        
        # Process the command
        return await process_cli_command(bot)
    except Exception as e:
        logger.error(f"Error in CLI mode: {e}", exc_info=True)
        print(f"❌ Ошибка: {e}")
        return 1

def main():
    """Main entry point for the application."""
    # Check if running in CLI mode
    if len(sys.argv) > 1:
        return asyncio.run(run_cli())
    
    # Otherwise, run in bot mode
    from core.bot.bot import main as run_bot
    return run_bot()

def run():
    """Run the application."""
    try:
        return main()
    except KeyboardInterrupt:
        print("\n👋 До свидания!")
        return 0

if __name__ == "__main__":
    sys.exit(run())
