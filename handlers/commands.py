import logging
from telegram.ext import CommandHandler
from config import settings

logger = logging.getLogger(__name__)

async def start(update, context):
    """Обработчик команды /start"""
    await update.message.reply_text("Бот запущен!")

async def help_cmd(update, context):
    """Обработчик команды /help"""
    await update.message.reply_text("Помощь по боту")

async def analyze_cmd(update, context):
    """Обработчик команды /analyze"""
    await update.message.reply_text("Анализ проекта")

def register(application):
    """Регистрация командных обработчиков"""
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_cmd))
    application.add_handler(CommandHandler("analyze", analyze_cmd))
    logger.info("Командные обработчики зарегистрированы")