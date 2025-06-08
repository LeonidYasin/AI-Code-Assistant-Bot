#!/usr/bin/env python3
import logging
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters
)
from config import config
from core.llm.client import LLMClient
from handlers.commands import setup_commands
from handlers.messages import handle_message
from handlers.callbacks import button_callback

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class CodeAssistantBot:
    def __init__(self):
        self.llm_client = LLMClient()
        self.application = None

    async def post_init(self, app):
        """Действия после инициализации"""
        await app.bot.set_my_commands([
            ("start", "Запуск бота"),
            ("help", "Помощь по командам"),
            ("analyze", "Анализ проекта")
        ])
        logger.info("Бот успешно инициализирован")

    def setup_handlers(self):
        """Регистрация всех обработчиков"""
        # Команды (/start, /help и т.д.)
        setup_commands(self.application)

        # Обычные текстовые сообщения
        self.application.add_handler(
            MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                handle_message
            )
        )

        # Callback-кнопки
        self.application.add_handler(
            CallbackQueryHandler(button_callback)
        )

    async def run(self):
        """Запуск бота"""
        try:
            # Инициализация LLM клиента
            self.llm_client.initialize(use_gigachat=True)

            # Создание Telegram приложения
            self.application = (
                Application.builder()
                .token(config.TELEGRAM_TOKEN)
                .post_init(self.post_init)
                .build()
            )

            # Настройка обработчиков
            self.setup_handlers()

            logger.info("Бот запущен в режиме polling...")
            await self.application.run_polling()

        except Exception as e:
            logger.critical(f"Критическая ошибка: {e}")
            raise

if __name__ == "__main__":
    bot = CodeAssistantBot()
    
    try:
        import asyncio
        asyncio.run(bot.run())
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")