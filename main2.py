import logging
from telegram.ext import ApplicationBuilder
from config import settings
from core.llm.client import LLMClient
from handlers import messages

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

llm_client = LLMClient(model="latest")

async def main():
    app = ApplicationBuilder().token(settings.TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT, messages.handle_message))
    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())