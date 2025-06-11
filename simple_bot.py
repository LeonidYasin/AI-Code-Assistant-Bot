import os
import logging
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackContext,
)
from dotenv import load_dotenv

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Обработчики команд
async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text("👋 Привет! Я простой тестовый бот!")

async def help_command(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text("ℹ️ Доступные команды: /start, /help")

async def echo(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text(f"Вы написали: {update.message.text}")

def main() -> None:
    # Загрузка переменных окружения
    load_dotenv()
    
    # Получение токена
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.error("Не задан TELEGRAM_BOT_TOKEN в переменных окружения")
        return

    # Создание приложения
    application = (
        Application.builder()
        .token(token)
        .connect_timeout(30.0)
        .read_timeout(30.0)
        .build()
    )

    # Регистрация обработчиков
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    # Запуск бота
    logger.info("Бот запущен...")
    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
