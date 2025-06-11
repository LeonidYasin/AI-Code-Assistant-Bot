import os
import asyncio
import logging
from telegram import Bot
from dotenv import load_dotenv

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def main():
    # Загрузка переменных окружения
    load_dotenv()
    
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        logger.error('Не задан TELEGRAM_BOT_TOKEN в переменных окружения')
        return
    
    bot = Bot(token=token)
    
    # Получаем информацию о боте
    me = await bot.get_me()
    logger.info(f"Бот: @{me.username} (ID: {me.id})")
    
    # Проверяем вебхук
    webhook_info = await bot.get_webhook_info()
    logger.info(f"Информация о вебхуке: {webhook_info}")
    
    if webhook_info.url:
        logger.info("Удаляем вебхук...")
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("Вебхук успешно удален")
    
    # Получаем обновления
    logger.info("Проверяем обновления...")
    updates = await bot.get_updates(timeout=10, limit=10)
    
    if updates:
        logger.info(f"Найдено {len(updates)} обновлений:")
        for update in updates:
            logger.info(f"Update ID: {update.update_id}")
            if update.message:
                logger.info(f"  Сообщение от {update.message.from_user.username}: {update.message.text}")
    else:
        logger.info("Обновлений не найдено")

if __name__ == "__main__":
    asyncio.run(main())
