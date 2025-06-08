import os
from config import config


import re
import logging
from typing import Optional
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, filters
from config import config
from core.llm.client import llm_client
from core.code_generator.python_gen import PythonGenerator, CodeTask
from core.project.analyzer import analyze_project
from core.utils import (
    save_code,
    validate_python_code,
    safe_execute_command
)
from core.project.executor import (
    run_script,
    run_cmd,
    install_dependencies
)

logger = logging.getLogger(__name__)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Основной обработчик текстовых сообщений"""
    chat_id = update.message.chat_id
    message_text = update.message.text.strip()
    lower_text = message_text.lower()

    try:
        # 1. Команда "создай"
        if lower_text.startswith(('создай', 'напиши')):
            await handle_create_command(update, context, message_text)
        
        # 2. Команда "исправить"
        elif lower_text.startswith(('исправить', 'почини')):
            await handle_fix_command(update, context, message_text)
        
        # 3. Команда "запустить"
        elif lower_text.startswith('запусти'):
            await handle_run_command(update, context, message_text)
        
        # 4. Системные команды (cmd:)
        elif lower_text.startswith('cmd:'):
            await handle_system_command(update, context, message_text)
        
        # 5. Общие запросы к ИИ
        else:
            await handle_ai_request(update, context, message_text)

    except Exception as e:
        logger.error(f"Ошибка обработки сообщения: {e}")
        await update.message.reply_text(f"⚠️ Произошла ошибка: {str(e)}")

async def handle_create_command(
    update: Update, 
    context: ContextTypes.DEFAULT_TYPE,
    message_text: str
):
    """Обработка команд вида 'создай file.py описание'"""
    match = re.match(r"(?:создай|напиши)\s+(\S+)\s+(.+)", message_text, re.IGNORECASE)
    if not match:
        await update.message.reply_text(
            "❌ Формат: `/создай файл.py описание`\n"
            "Пример: `/создай api.py Flask REST API`",
            parse_mode="Markdown"
        )
        return

    file_name, task_description = match.groups()
    if not file_name.endswith('.py'):
        file_name += '.py'

    project_context = analyze_project(config.PROJECT_DIR)
    generator = PythonGenerator(llm_client)
    
    status, result = generator.generate(
        CodeTask(
            description=task_description,
            context=project_context
        )
    )

    if status == "error":
        await update.message.reply_text(f"❌ Ошибка генерации:\n{result}")
        return

    output_path = f"{config.PROJECT_DIR}/{file_name}"
    success, save_result = save_code(result, output_path)

    if success:
        response = (
            f"✅ Код сохранён в `{output_path}`\n\n"
            f"```python\n{result[:300]}\n```\n"
            f"... [показаны первые 300 символов]"
        )
        await update.message.reply_text(
            response,
            parse_mode="MarkdownV2"
        )
        await run_script(output_path, update.message.chat_id, context)
    else:
        await update.message.reply_text(f"❌ Ошибка сохранения:\n{save_result}")

async def handle_fix_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    message_text: str
):
    """Обработка команд вида 'исправить file.py'"""
    file_name = re.sub(r"(?:исправить|почини)\s+", "", message_text, flags=re.IGNORECASE).strip()
    file_path = f"{config.PROJECT_DIR}/{file_name}"

    if not file_path.endswith('.py'):
        file_path += '.py'

    if not os.path.exists(file_path):
        await update.message.reply_text(f"❌ Файл {file_path} не найден")
        return

    with open(file_path, "r", encoding="utf-8") as f:
        original_code = f.read()

    # Запускаем код для получения ошибок
    result = safe_execute_command(f"python {file_path}")
    if not result.get("error"):
        await update.message.reply_text("✅ Код выполняется без ошибок")
        return

    project_context = analyze_project(config.PROJECT_DIR)
    fix_prompt = (
        f"Исправь ошибки в коде:\n{original_code}\n\n"
        f"Ошибка при выполнении:\n{result['error']}\n\n"
        f"Контекст проекта:\n{project_context}"
    )

    fixed_code = llm_client.call(fix_prompt)
    is_valid, validation_error = validate_python_code(fixed_code)

    if not is_valid:
        await update.message.reply_text(
            f"❌ Исправленный код содержит ошибки:\n{validation_error}"
        )
        return

    success, save_result = save_code(fixed_code, file_path)
    if success:
        response = (
            f"✅ Код исправлен и сохранён:\n\n"
            f"```python\n{fixed_code[:300]}\n```\n"
            f"... [показаны первые 300 символов]"
        )
        await update.message.reply_text(response, parse_mode="MarkdownV2")
    else:
        await update.message.reply_text(f"❌ Ошибка сохранения:\n{save_result}")

async def handle_run_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    message_text: str
):
    """Обработка команд вида 'запусти file.py'"""
    file_name = re.sub(r"запусти\s+", "", message_text, flags=re.IGNORECASE).strip()
    file_path = f"{config.PROJECT_DIR}/{file_name}"

    if not file_path.endswith('.py'):
        file_path += '.py'

    if not os.path.exists(file_path):
        await update.message.reply_text(f"❌ Файл {file_path} не найден")
        return

    await run_script(file_path, update.message.chat_id, context)

async def handle_system_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    message_text: str
):
    """Обработка системных команд (cmd: ...)"""
    command = message_text[4:].strip()
    allowed = any(
        command.startswith(cmd) 
        for cmd in config.SAFE_COMMANDS
    )

    if not allowed:
        await update.message.reply_text(
            "❌ Команда не разрешена. Разрешены:\n" +
            "\n".join(f"- {cmd}" for cmd in config.SAFE_COMMANDS)
        )
        return

    await run_cmd(command, update.message.chat_id, context)

async def handle_ai_request(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    message_text: str
):
    """Обработка общих запросов к ИИ"""
    project_context = analyze_project(config.PROJECT_DIR)
    prompt = f"Запрос: {message_text}\nКонтекст проекта:\n{project_context}"
    
    response = llm_client.call(prompt)
    await update.message.reply_text(
        response[:4000],  # Ограничение Telegram
        parse_mode="Markdown"
    )