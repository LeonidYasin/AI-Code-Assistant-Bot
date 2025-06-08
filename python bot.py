import os
import requests
import subprocess
import json
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import ast  # Для проверки синтаксиса
import re

# Настройки
BOT_HUB_API_URL = "https://bothub.chat/api/v2/openai/v1/chat/completions"
BOT_HUB_API_KEY = "ваш_ключ_от_bothub"
TELEGRAM_TOKEN = "ваш_токен_телеграм_бота"
PROJECT_DIR = "./my_project"
ALLOWED_EXTENSIONS = {".py", ".json", ".yaml", ".md"}  # Поддерживаемые файлы
SAFE_COMMANDS = ["dir", "pip install", "python", "git"]  # Белый список CMD

# Анализ проекта
def analyze_project(directory):
    context = ""
    for root, _, files in os.walk(directory):
        if "venv" in root or "__pycache__" in root:
            continue
        for file in files:
            if os.path.splitext(file)[1] in ALLOWED_EXTENSIONS:
                with open(os.path.join(root, file), "r", encoding="utf-8") as f:
                    context += f"File: {file}\n{f.read()}\n\n"
    # Ограничение контекста (например, 50K символов)
    if len(context) > 50000:
        context = context[:50000] + "\n[Контекст обрезан из-за лимита]"
    return context

# Запрос к BotHub API
def call_bothub(prompt, context=""):
    try:
        response = requests.post(
            BOT_HUB_API_URL,
            json={
                "model": "claude-3-7-sonnet",
                "messages": [{"role": "user", "content": f"Контекст:\n{context}\nЗадача: {prompt}"}],
                "max_tokens": 1000
            },
            headers={"Authorization": f"Bearer {BOT_HUB_API_KEY}"}
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except requests.exceptions.RequestException as e:
        return f"Ошибка API: {e}"

# Проверка синтаксиса Python
def is_valid_python(code):
    try:
        ast.parse(code)
        return True
    except SyntaxError:
        return False

# Сохранение кода
def save_code(code, output_file):
    if is_valid_python(code):
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(code)
        return True, output_file
    else:
        return False, "Синтаксическая ошибка в коде"

# Установка зависимостей
def install_dependencies(requirements_file):
    if os.path.exists(requirements_file):
        subprocess.run(f"pip install -r {requirements_file}", shell=True)

# Запуск скрипта с одобрением
def run_script(file_path, chat_id, context):
    if os.path.exists(file_path):
        context.bot.send_message(
            chat_id=chat_id,
            text=f"Запустить {file_path}?",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Да", callback_data=f"run_script:{file_path}"),
                 InlineKeyboardButton("Нет", callback_data="cancel")]
            ])
        )
        context.user_data["action"] = "run_script"
    else:
        context.bot.send_message(chat_id=chat_id, text="Файл не найден.")

# Выполнение команды CMD с одобрением
def run_cmd(command, chat_id, context):
    if any(command.startswith(cmd) for cmd in SAFE_COMMANDS):
        context.bot.send_message(
            chat_id=chat_id,
            text=f"Выполнить команду: {command}?",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Да", callback_data=f"run_cmd:{command}"),
                 InlineKeyboardButton("Нет", callback_data="cancel")]
            ])
        )
        context.user_data["action"] = "run_cmd"
    else:
        context.bot.send_message(chat_id=chat_id, text="Команда не в белом списке!")

# Telegram-бот
def start(update, context):
    update.message.reply_text(
        "Привет! Отправь задачу, например:\n"
        "- Создай <файл> <задача>\n"
        "- Запустить <файл>\n"
        "- cmd: <команда>\n"
        "- Исправить ошибки <файл>"
    )

def handle_message(update, context):
    chat_id = update.message.chat_id
    message = update.message.text.lower()

    # Анализ проекта
    context_str = analyze_project(PROJECT_DIR)

    # Обработка команд
    if message.startswith("создай"):
        match = re.match(r"создай\s+(\S+)\s+(.+)", message)
        if match:
            output_file, task = match.groups()
            output_path = os.path.join(PROJECT_DIR, output_file)
            code = call_bothub(task, context_str)
            success, result = save_code(code, output_path)
            if success:
                update.message.reply_text(f"Код сохранён в {result}:\n{code}")
                run_script(output_path, chat_id, context)
            else:
                update.message.reply_text(result)
        else:
            update.message.reply_text("Укажи имя файла и задачу, например: 'Создай api.py Flask API'")
    elif message.startswith("запустить"):
        file_path = os.path.join(PROJECT_DIR, message.split()[-1])
        run_script(file_path, chat_id, context)
    elif message.startswith("cmd:"):
        command = message[4:].strip()
        run_cmd(command, chat_id, context)
    elif message.startswith("исправить ошибки"):
        file_path = os.path.join(PROJECT_DIR, message.split()[-1])
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                code = f.read()
            result = subprocess.run(f"python {file_path}", capture_output=True, text=True, shell=True)
            if result.stderr:
                fixed_code = call_bothub(f"Исправь ошибки в коде:\n{code}\nОшибки:\n{result.stderr}", context_str)
                success, result = save_code(fixed_code, file_path)
                update.message.reply_text(f"Исправленный код сохранён в {result}:\n{fixed_code}" if success else result)
            else:
                update.message.reply_text("Ошибок не найдено.")
        else:
            update.message.reply_text("Файл не найден.")
    else:
        response = call_bothub(message, context_str)
        update.message.reply_text(response)

def button_callback(update, context):
    query = update.callback_query
    query.answer()
    chat_id = query.message.chat_id
    data = query.data

    if data == "cancel":
        context.bot.send_message(chat_id=chat_id, text="Действие отменено.")
        context.user_data.clear()
    elif data.startswith("run_script:"):
        file_path = data.split(":", 1)[1]
        install_dependencies(os.path.join(PROJECT_DIR, "requirements.txt"))
        result = subprocess.run(f"python {file_path}", capture_output=True, text=True, shell=True)
        context.bot.send_message(chat_id=chat_id, text=f"Результат:\n{result.stdout}\nОшибки:\n{result.stderr}")
        context.user_data.clear()
    elif data.startswith("run_cmd:"):
        command = data.split(":", 1)[1]
        result = subprocess.run(command, capture_output=True, text=True, shell=True)
        context.bot.send_message(chat_id=chat_id, text=f"Результат:\n{result.stdout}\nОшибки:\n{result.stderr}")
        context.user_data.clear()

def main():
    updater = Updater(TELEGRAM_TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    dp.add_handler(CallbackQueryHandler(button_callback))
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
