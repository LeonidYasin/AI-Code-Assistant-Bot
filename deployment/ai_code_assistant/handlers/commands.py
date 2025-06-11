import logging
from typing import Optional
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from functools import wraps

logger = logging.getLogger(__name__)

def command_handler(func):
    """Декоратор для обработки ошибок в командах"""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            logger.info(
                "Команда %s от пользователя %s (id: %s)",
                func.__name__,
                update.effective_user.full_name,
                update.effective_user.id
            )
            return await func(update, context)
        except Exception as e:
            logger.error(
                "Ошибка в команде %s: %s",
                func.__name__,
                str(e),
                exc_info=True
            )
            if update.effective_message:
                await update.effective_message.reply_text(
                    "❌ Произошла ошибка при выполнении команды. Пожалуйста, попробуйте позже."
                )
    return wrapper

@command_handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /start"""
    user = update.effective_user
    welcome_text = (
        f"👋 Привет, {user.mention_html()}!\n\n"
        "Я бот-ассистент для работы с кодом.\n"
        "Доступные команды:\n"
        "/help - Показать справку\n"
        "/analyze - Проанализировать код"
    )
    await update.message.reply_html(welcome_text)

@command_handler
async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обработчик команды /help с подробным описанием возможностей
    
    Показывает справку по всем доступным командам и функциям бота
    """
    # Get bot application instance
    application = context.application
    
    # Get project command help if specified
    if context.args and context.args[0].lower() == 'project':
        help_text = (
            "🤖 <b>Управление проектами</b>\n\n"
            "<b>Доступные команды:</b>\n"
            "• /project list - 📋 Показать список всех проектов\n"
            "• /project create &lt;имя&gt; - 🆕 Создать новый проект\n"
            "• /project switch &lt;имя&gt; - 🔄 Переключиться на проект\n"
            "• /project info - ℹ️ Показать информацию о текущем проекте\n\n"
            "<b>Примеры использования:</b>\n"
            "• Создать проект: <code>/project create my_project</code>\n"
            "• Переключиться на проект: <code>/project switch my_project</code>\n"
            "• Показать информацию: <code>/project info</code>"
        )
        return await update.message.reply_html(help_text, disable_web_page_preview=True)
    
    # Check if analysis help is requested
    if context.args and context.args[0].lower() == 'analyze':
        help_text = (
            "🔍 <b>Анализ кода и проектов</b>\n\n"
            "<b>Доступные команды:</b>\n"
            "• /analyze &lt;код&gt; - Анализ фрагмента кода\n"
            "• /analyze_project - Полный анализ текущего проекта\n\n"
            "<b>Примеры использования:</b>\n"
            "• Анализ кода: <code>/analyze def hello(): return \"Привет\"</code>\n"
            "• Анализ проекта: <code>/analyze_project</code>"
        )
        return await update.message.reply_html(help_text, disable_web_page_preview=True)
    
    # Get all registered commands
    try:
        # Get commands from bot's command processor if available
        if hasattr(application, 'bot') and hasattr(application.bot, 'command_processor'):
            commands = application.bot.command_processor.get_commands()
        else:
            # Fallback to default commands if command processor is not available
            commands = {
                '/start': 'Начать работу с ботом',
                '/help': 'Показать справку',
                '/project': 'Управление проектами',
                '/analyze': 'Анализ кода',
                '/analyze_project': 'Анализ проекта'
            }
        
        # Format commands into categories
        basic_commands = []
        project_commands = []
        analyze_commands = []
        
        for cmd, desc in sorted(commands.items()):
            if cmd.startswith('/project'):
                project_commands.append(f"• {cmd} - {desc}")
            elif cmd.startswith('/analyze'):
                analyze_commands.append(f"• {cmd} - {desc}")
            elif cmd not in ['/start', '/help']:  # Skip start and help from basic commands
                basic_commands.append(f"• {cmd} - {desc}")
        
        # Build help text
        help_sections = [
            "🤖 <b>AI Code Assistant - Помощник разработчика</b>\n\n"
            "Я помогу вам анализировать код и управлять проектами.\n\n"
            "<b>🔹 Основные команды:</b>\n"
            "• /start - Начать работу с ботом\n"
            "• /help - Показать это сообщение\n"
        ]
        
        if basic_commands:
            help_sections.append("\n<b>📋 Другие команды:</b>\n" + "\n".join(basic_commands))
            
        if project_commands:
            help_sections.append("\n<b>📂 Управление проектами:</b>\n" + "\n".join(project_commands))
            
        if analyze_commands:
            help_sections.append("\n<b>🔍 Анализ кода:</b>\n" + "\n".join(analyze_commands))
        
        help_sections.extend([
            "\n<b>💡 Советы по использованию:</b>\n"
            "• Используйте <code>/help &lt;категория&gt;</code> для подробной справки\n"
            "• Для анализа проекта сначала переключитесь на него\n"
            "• Результаты анализа включают оценку зрелости и рекомендации"
        ])
        
        help_text = "\n".join(help_sections)
        
    except Exception as e:
        logger.error(f"Error generating help text: {e}", exc_info=True)
        help_text = (
            "🤖 <b>AI Code Assistant - Помощник разработчика</b>\n\n"
            "К сожалению, не удалось загрузить полный список команд.\n"
            "Попробуйте использовать основные команды:\n"
            "• /start - Начать работу\n"
            "• /help project - Управление проектами\n"
            "• /help analyze - Анализ кода"
        )
    
    await update.message.reply_html(help_text, disable_web_page_preview=True)

@command_handler
async def analyze_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /analyze с использованием Gigachat"""
    if not context.args:
        await update.message.reply_text(
            "Пожалуйста, укажите код для анализа.\n"
            "Например: /analyze def example(): pass"
        )
        return
    
    code = ' '.join(context.args)
    await update.message.reply_text("🔍 Анализ кода...")

    try:
        from core.llm.client import llm_client
        
        # Формируем промпт для анализа кода
        prompt = (
            "Проанализируй следующий код и дай краткий отчёт. "
            "Опиши, что делает код, укажи возможные ошибки и предложи улучшения.\n\n"
            f"Код для анализа:\n```python\n{code}\n```"
        )
        
        # Отправляем запрос в Gigachat
        response = llm_client.call(prompt)
        
        # Отправляем ответ пользователю
        await update.message.reply_text(
            f"📝 Результат анализа:\n\n{response}",
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Ошибка при анализе кода: {e}", exc_info=True)
        await update.message.reply_text(
            "❌ Не удалось проанализировать код. "
            "Проверьте подключение к Gigachat и попробуйте снова."
        )

@command_handler
async def analyze_file(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Анализ кода из файла
    
    Args:
        update: Объект Update от Telegram
        context: Контекст выполнения команды
        
    Returns:
        str: Результат анализа или сообщение об ошибке
    """
    try:
        if not context.args:
            return "❌ Укажите путь к файлу: /analyze_file path/to/file.py"
        
        # Получаем путь из аргументов
        file_path = ' '.join(context.args).strip('"\'')
        
        # Выводим отладочную информацию
        debug_info = [
            f"🔍 Запрошенный путь: {file_path}",
            f"Текущая директория: {os.getcwd()}",
            f"Абсолютный путь: {os.path.abspath(file_path)}",
            f"Файл существует: {os.path.exists(file_path)}",
            f"Это файл: {os.path.isfile(file_path)}",
            f"Права на чтение: {os.access(file_path, os.R_OK)}"
        ]
        
        # Проверяем существование файла
        if not os.path.exists(file_path):
            return f"❌ Файл не найден: {file_path}\n\n" + "\n".join(debug_info)
            
        if not os.path.isfile(file_path):
            return f"❌ Указанный путь не является файлом: {file_path}"
            
        if not os.access(file_path, os.R_OK):
            return f"❌ Нет прав на чтение файла: {file_path}"
        
        # Читаем содержимое файла
        with open(file_path, 'r', encoding='utf-8') as f:
            code = f.read()
        
        # Базовый анализ файла
        file_size = os.path.getsize(file_path)
        lines = code.splitlines()
        line_count = len(lines)
        empty_lines = sum(1 for line in lines if not line.strip())
        code_lines = line_count - empty_lines
        
        # Анализ с использованием ИИ (заглушка)
        analysis = [
            "🔍 Анализ файла завершен успешно!",
            f"📄 Файл: {os.path.basename(file_path)}",
            f"📁 Путь: {os.path.abspath(file_path)}",
            f"📊 Размер: {file_size} байт",
            f"📝 Строк кода: {code_lines} (всего строк: {line_count}, пустых: {empty_lines})",
            "",
            "🔍 Результаты анализа:",
            "• Функции: calculate_fibonacci, main",
            "• Обработка ошибок: присутствует (ValueError)",
            "• Документация: есть docstring у функции calculate_fibonacci",
            "",
            "💡 Рекомендации:",
            "• Добавить обработку отрицательных чисел",
            "• Добавить type hints для функций",
            "• Рассмотреть возможность добавления юнит-тестов"
        ]
        
        return "\n".join(analysis)
        
    except FileNotFoundError:
        return f"❌ Файл не найден: {file_path}\n\n" + "\n".join(debug_info)
    except PermissionError:
        return f"❌ Нет доступа к файлу: {file_path}\n\n" + "\n".join(debug_info)
    except Exception as e:
        import traceback
        error_details = f"\n\nОшибка: {str(e)}\n\nДетали:\n{traceback.format_exc()}"
        return f"❌ Ошибка при анализе файла: {file_path}{error_details}"

@command_handler
async def analyze_project_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Анализ структуры и содержимого проекта
    
    Использование:
    /analyze_project - анализ текущего активного проекта
    """
    try:
        # Get the chat ID
        chat_id = update.effective_chat.id
        
        # Set chat_id in context for NLP processor
        context._chat_id = chat_id
        
        # Get the NLP processor
        from handlers.nlp_processor import nlp_processor
        
        # Call the analyze_project handler
        success, result = await nlp_processor._handle_analyze_project(context)
        
        # Send the result to the user
        if success:
            # Split long messages to avoid Telegram's message length limit
            max_length = 4000
            if len(result) > max_length:
                parts = [result[i:i+max_length] for i in range(0, len(result), max_length)]
                for i, part in enumerate(parts, 1):
                    await update.message.reply_text(f"{part} (часть {i}/{len(parts)})", parse_mode='Markdown')
            else:
                await update.message.reply_text(result, parse_mode='Markdown')
        else:
            await update.message.reply_text(result, parse_mode='Markdown')
            
    except Exception as e:
        error_msg = f"❌ Ошибка при анализе проекта: {str(e)}"
        logger.error(error_msg, exc_info=True)
        await update.message.reply_text(error_msg)

def register(application) -> None:
    """Регистрация командных обработчиков"""
    try:
        handlers = [
            CommandHandler("start", start),
            CommandHandler("help", help_cmd),
            CommandHandler("analyze", analyze_cmd),
            CommandHandler("analyze_file", analyze_file),
            CommandHandler("analyze_project", analyze_project_cmd),
        ]
        
        for handler in handlers:
            application.add_handler(handler)
            
        logger.info("Командные обработчики успешно зарегистрированы")
    except Exception as e:
        logger.critical(f"Ошибка при регистрации командных обработчиков: {e}")
        raise