import logging
import subprocess
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackContext, CallbackQueryHandler
from config import settings
from core.utils import safe_execute_command

logger = logging.getLogger(__name__)

async def button_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    try:
        data = query.data
        chat_id = query.message.chat_id

        if data == "cancel":
            await context.bot.send_message(chat_id=chat_id, text="❌ Действие отменено")
            context.user_data.clear()
        
        elif data.startswith("run_script:"):
            file_path = data.split(":", 1)[1]
            output = safe_execute_command(f"python {file_path}")
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"🔄 Результат выполнения:\n{output[:4000]}"
            )
        
        elif data.startswith("run_cmd:"):
            command = data.split(":", 1)[1]
            if any(cmd in command for cmd in settings.SAFE_COMMANDS):
                output = safe_execute_command(command)
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=f"💻 Выполнено:\n{output[:4000]}"
                )
            else:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text="⛔ Команда не разрешена!"
                )
    
    except Exception as e:
        logger.error(f"Callback error: {e}")
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"⚠️ Ошибка: {str(e)}"
        )

# Создаем обработчик колбэков
handler = CallbackQueryHandler(button_callback)