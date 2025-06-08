import subprocess
import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

logger = logging.getLogger(__name__)

def run_script(file_path: str, chat_id: int, context):
    if not os.path.exists(file_path):
        context.bot.send_message(chat_id=chat_id, text="❌ Файл не найден")
        return

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Да", callback_data=f"run_script:{file_path}")],
        [InlineKeyboardButton("Нет", callback_data="cancel")]
    ])
    context.bot.send_message(
        chat_id=chat_id,
        text=f"Запустить {file_path}?",
        reply_markup=keyboard
    )