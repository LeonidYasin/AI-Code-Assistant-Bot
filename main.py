#!/usr/bin/env python3
import logging
import asyncio
import sys
from telegram.ext import Application

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

async def setup_bot():
    """Настройка и запуск бота"""
    application = Application.builder().token("ВАШ_TELEGRAM_ТОКЕН").build()
    
    # Здесь регистрируем обработчики
    from handlers import commands, messages, callbacks
    commands.register(application)
    application.add_handler(messages.handler)
    application.add_handler(callbacks.handler)
    
    await application.initialize()
    await application.start()
    logger.info("Бот успешно запущен")
    
    # Бесконечный цикл для работы бота
    while True:
        await asyncio.sleep(3600)  # Проверка каждые 3600 секунд (1 час)

async def shutdown_bot(app):
    """Корректное завершение работы"""
    await app.stop()
    await app.shutdown()
    logger.info("Бот остановлен")

def main():
    """Точка входа"""
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        app = loop.run_until_complete(setup_bot())
        loop.run_forever()
    except KeyboardInterrupt:
        logger.info("Получен сигнал завершения")
        loop.run_until_complete(shutdown_bot(app))
    except Exception as e:
        logger.critical(f"Критическая ошибка: {e}")
    finally:
        loop.close()

if __name__ == "__main__":
    main()