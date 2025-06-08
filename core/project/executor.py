import os
import subprocess
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from config import settings
from core.utils import safe_execute_command
import logging

logger = logging.getLogger(__name__)

async def run_script(file_path: str, chat_id: int, context):
    """Запускает Python-скрипт с подтверждением"""
    if not os.path.exists(file_path):
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"❌ Файл {file_path} не найден"
        )
        return

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Запустить", callback_data=f"run_script:{file_path}")],
        [InlineKeyboardButton("❌ Отмена", callback_data="cancel")]
    ])

    await context.bot.send_message(
        chat_id=chat_id,
        text=f"Запустить скрипт?\n`{file_path}`",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

async def run_cmd(command: str, chat_id: int, context):
    """Выполняет shell-команду с подтверждением"""
    if not any(command.startswith(cmd) for cmd in settings.SAFE_COMMANDS):
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ Команда не разрешена!\nРазрешены: " + ", ".join(settings.SAFE_COMMANDS)
        )
        return

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Выполнить", callback_data=f"run_cmd:{command}")],
        [InlineKeyboardButton("❌ Отмена", callback_data="cancel")]
    ])

    await context.bot.send_message(
        chat_id=chat_id,
        text=f"Выполнить команду?\n`{command}`",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

async def install_dependencies(requirements_file: str = "requirements.txt"):
    """Устанавливает зависимости из файла"""
    if os.path.exists(requirements_file):
        result = safe_execute_command(f"pip install -r {requirements_file}")
        if not result["success"]:
            logger.error(f"Ошибка установки зависимостей: {result['error']}")