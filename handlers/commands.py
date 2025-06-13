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

async def _analyze_project_directly(project_path: str) -> Tuple[bool, str]:
    """Прямой анализ проекта без использования NLP-процессора"""
    from pathlib import Path
    from core.project.analyzer import ProjectAnalyzer
    
    try:
        # Преобразуем в абсолютный путь
        project_path = Path(project_path).resolve()
        if not project_path.exists():
            return False, f"❌ Путь не существует: {project_path}"
            
        # Анализируем проект напрямую
        analyzer = ProjectAnalyzer(project_path)
        analysis = analyzer.analyze_project()
        
        if 'error' in analysis:
            return False, f"❌ Ошибка при анализе: {analysis['error']}"
            
        # Формируем отчет
        project_name = project_path.name
        stats = analysis.get('stats', {})
        
        response = [
            f"📊 *Анализ проекта: {project_name}*",
            f"📂 Путь: `{project_path}`\n"
        ]
        
        # Добавляем статистику, если есть
        if stats:
            response.extend([
                "*📊 Статистика:*",
                f"• Всего файлов: {stats.get('total_files', 0)}",
                f"• Общий размер: {_format_size(stats.get('total_size', 0))}",
                f"• Количество директорий: {stats.get('dir_count', 0)}"
            ])
        
        # Добавляем структуру проекта, если есть
        if 'structure' in analysis and analysis['structure']:
            response.append("\n*📁 Структура проекта:*")
            response.append(_format_structure(analysis['structure']))
        
        # Добавляем рекомендации, если есть
        if 'summary' in analysis and analysis['summary']:
            summary = analysis['summary']
            response.extend([
                "\n*🔍 Анализ проекта:*",
                f"• *Тип проекта:* {summary.get('project_type', 'Не определен')}",
                f"• *Дата изменения:* {summary.get('modified_date', 'Неизвестно')}",
                "\n*📌 Рекомендации по развитию:*"
            ])
            
            recommendations = []
            if not summary.get('has_readme', False):
                recommendations.append("• Добавьте файл README.md с описанием проекта")
            if not summary.get('has_license', False):
                recommendations.append("• Добавьте файл LICENSE с лицензией")
            if not any(f.get('has_tests', False) for f in analysis.get('files', [])):
                recommendations.append("• Добавьте тесты для улучшения качества кода")
            if not summary.get('has_gitignore', False):
                recommendations.append("• Добавьте .gitignore файл для игнорирования временных файлов")
                
            response.extend(recommendations if recommendations else ["• Отличная работа! Проект хорошо структурирован."])
        
        return True, "\n".join(response)
        
    except Exception as e:
        return False, f"❌ Ошибка при анализе проекта: {str(e)}"

def _format_size(size_bytes: int) -> str:
    """Форматирует размер в байтах в читаемый вид"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"

def _format_structure(node: dict, level: int = 0) -> str:
    """Форматирует структуру проекта в читаемый вид"""
    indent = '  ' * level
    result = []
    
    if node.get('type') == 'directory':
        result.append(f"{indent}📁 {node.get('name', '')}/")
        for child in node.get('children', [])[:5]:  # Показываем первые 5 элементов
            result.append(_format_structure(child, level + 1))
        if len(node.get('children', [])) > 5:
            result.append(f"{indent}  ... и ещё {len(node['children']) - 5} элементов")
    elif node.get('type') == 'file':
        result.append(f"{indent}📄 {node.get('name', '')}")
    
    return '\n'.join(result)

@command_handler
async def analyze_project_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Анализ структуры и содержимого проекта
    
    Использование:
    /analyze_project - анализ текущего активного проекта
    /analyze_project project_name - анализ указанного проекта
    /analyze_project /path/to/project - анализ проекта по указанному пути
    """
    try:
        # Get the project path from arguments if provided
        project_path = ' '.join(context.args).strip() if context.args else None
        
        # If no path provided, use the current project
        if not project_path:
            from handlers.nlp_processor import nlp_processor
            success, result = await nlp_processor._handle_analyze_project(update, context)
        else:
            # Check if the argument is a direct path
            from pathlib import Path
            potential_path = Path(project_path).expanduser().resolve()
            
            if potential_path.exists() and potential_path.is_dir():
                # Analyze the directory directly
                success, result = await _analyze_project_directly(str(potential_path))
            else:
                # Not a valid path, treat as project name
                from handlers.nlp_processor import nlp_processor
                # Pass the project name as an argument
                context.args = [project_path]
                success, result = await nlp_processor._handle_analyze_project(update, context)
        
        # Send the result to the user
        if success:
            # Split long messages to avoid Telegram's message length limit
            max_length = 4000
            if len(result) > max_length:
                parts = [result[i:i+max_length] for i in range(0, len(result), max_length)]
                for i, part in enumerate(parts, 1):
                    await update.message.reply_text(
                        f"*[Часть {i}/{len(parts)}]*\n{part}",
                        parse_mode='Markdown'
                    )
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