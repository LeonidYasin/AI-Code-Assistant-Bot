import logging
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from core.llm.client import llm_client
from core.project.analyzer import analyze_project

logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    help_text = (
        "🤖 *AI Code Assistant*\n\n"
        "Доступные команды:\n"
        "• `/создай файл.py описание` – генерация кода\n"
        "• `/исправить файл.py` – исправление ошибок\n"
        "• `/запустить файл.py` – выполнение скрипта\n"
        "• `cmd: команда` – выполнение shell-команды\n\n"
        "Пример:\n"
        "`/создай api.py Flask REST API с JWT`"
    )
    
    await update.message.reply_text(
        help_text,
        parse_mode="MarkdownV2"
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help"""
    await update.message.reply_text(
        "🆘 Помощь по использованию бота:\n"
        "Используйте /start для получения основной информации",
        parse_mode="Markdown"
    )

async def analyze_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /analyze (анализ проекта)"""
    project_context = analyze_project(config.PROJECT_DIR)
    summary = llm_client.call(
        "Кратко проанализируй структуру проекта:\n" + 
        project_context[:5000]  # Ограничение контекста
    )
    
    await update.message.reply_text(
        f"📊 Анализ проекта:\n\n{summary[:4000]}",
        parse_mode="Markdown"
    )

def setup_commands(application):
    """Регистрация обработчиков команд"""
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_cmd))
    application.add_handler(CommandHandler("analyze", analyze_cmd))