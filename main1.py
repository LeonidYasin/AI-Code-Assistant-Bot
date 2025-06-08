import os
import requests
import subprocess
import json
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import ast
import re
import logging
from typing import Optional
from dotenv import load_dotenv
from langchain_gigachat.chat_models import GigaChat
from langchain_core.language_models import BaseChatModel

# Загрузка переменных окружения
load_dotenv()

# Настройки
class Config:
    def __init__(self):
        self.TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
        self.BOT_HUB_API_KEY = os.getenv("BOT_HUB_API_KEY")
        self.GIGACHAT_CREDS = {
            "model": "GigaChat-2-Max",
            "verify_ssl_certs": False,
            "credentials": os.getenv("GIGACHAT_CREDENTIALS")
        }
        self.USE_GIGACHAT = True  # По умолчанию используем GigaChat
        self.PROJECT_DIR = "./my_project"
        self.ALLOWED_EXTENSIONS = {".py", ".json", ".yaml", ".md"}
        self.SAFE_COMMANDS = ["dir", "pip install", "python", "git"]
        self.MAX_CONTEXT_LENGTH = 50000
        
        self.GIGACHAT_MODELS = {
            'lite': 'GigaChat-Lite',  # По умолчанию
            'base': 'GigaChat',
            'pro': 'GigaChat-Pro',
            'max': 'GigaChat-Max',
            'latest': 'GigaChat-2-Max'  # Актуальная на 2025 год
        }
        self.DEFAULT_GIGACHAT_MODEL = 'latest'  # Используем самую продвинутую

# Инициализация конфигурации
config = Config()

# Настройка логирования
logging.basicConfig(
    filename='llm_errors.log',
    level=logging.ERROR,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class LLMClient:
    def __init__(self):
        self._model: Optional[BaseChatModel] = None
    
    def initialize(self, use_gigachat: bool):
        """Инициализация LLM клиента"""
        try:
            if use_gigachat:
                self._model = GigaChat(**config.GIGACHAT_CREDS)
            else:
                self._model = BotHubWrapper(config.BOT_HUB_API_KEY)
        except Exception as e:
            logging.error(f"Ошибка инициализации LLM: {e}")
            raise
    
    def call(self, prompt: str, context: str = "") -> str:
        """Вызов LLM с обработкой ошибок"""
        if not self._model:
            raise ValueError("LLM не инициализирован")
        
        try:
            full_prompt = f"Контекст:\n{context}\nЗадача: {prompt}"
            response = self._model.invoke(full_prompt)
            return response.content
        except Exception as e:
            logging.error(f"Ошибка в LLM: {e}")
            return f"Произошла ошибка при обработке запроса: {str(e)}"

class BotHubWrapper:
    """Обёртка для BotHub API для совместимости с интерфейсом LangChain"""
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.api_url = "https://bothub.chat/api/v2/openai/v1/chat/completions"
    
    def invoke(self, prompt: str):
        try:
            response = requests.post(
                self.api_url,
                json={
                    "model": "claude-3-7-sonnet",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 1000
                },
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=30
            )
            response.raise_for_status()
            return type('obj', (object,), {
                'content': response.json()["choices"][0]["message"]["content"]
            })
        except Exception as e:
            logging.error(f"BotHub error: {e}")
            raise

def analyze_project(directory: str) -> str:
    """Анализ файлов проекта для контекста"""
    context = ""
    try:
        for root, _, files in os.walk(directory):
            if "venv" in root or "__pycache__" in root:
                continue
            for file in files:
                if os.path.splitext(file)[1] in config.ALLOWED_EXTENSIONS:
                    try:
                        with open(os.path.join(root, file), "r", encoding="utf-8") as f:
                            content = f.read()
                            context += f"File: {file}\n{content}\n\n"
                    except UnicodeDecodeError:
                        continue
        
        if len(context) > config.MAX_CONTEXT_LENGTH:
            context = context[:config.MAX_CONTEXT_LENGTH] + "\n[Контекст обрезан]"
        return context
    except Exception as e:
        logging.error(f"Ошибка анализа проекта: {e}")
        return ""

def is_valid_python(code: str) -> bool:
    """Проверка синтаксиса Python"""
    try:
        ast.parse(code)
        return True
    except SyntaxError as e:
        logging.warning(f"Синтаксическая ошибка: {e}")
        return False

def save_code(code: str, output_file: str) -> tuple:
    """Сохранение кода с проверкой синтаксиса"""
    if is_valid_python(code):
        try:
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(code)
            return True, output_file
        except Exception as e:
            logging.error(f"Ошибка сохранения файла: {e}")
            return False, f"Ошибка сохранения: {e}"
    return False, "Синтаксическая ошибка в коде"

def install_dependencies(requirements_file: str):
    """Установка зависимостей"""
    if os.path.exists(requirements_file):
        try:
            subprocess.run(
                f"pip install -r {requirements_file}",
                shell=True,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
        except subprocess.CalledProcessError as e:
            logging.error(f"Ошибка установки зависимостей: {e.stderr}")

def run_script(file_path: str, chat_id: int, context):
    """Запрос подтверждения на запуск скрипта"""
    if os.path.exists(file_path):
        context.bot.send_message(
            chat_id=chat_id,
            text=f"Запустить {file_path}?",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Да", callback_data=f"run_script:{file_path}"),
                [InlineKeyboardButton("Нет", callback_data="cancel")]
            ])
        )
        context.user_data["action"] = "run_script"
    else:
        context.bot.send_message(chat_id=chat_id, text="Файл не найден.")

def run_cmd(command: str, chat_id: int, context):
    """Запрос подтверждения на выполнение команды"""
    if any(command.startswith(cmd) for cmd in config.SAFE_COMMANDS):
        context.bot.send_message(
            chat_id=chat_id,
            text=f"Выполнить команду: {command}?",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Да", callback_data=f"run_cmd:{command}"),
                [InlineKeyboardButton("Нет", callback_data="cancel")]
            ])
        )
        context.user_data["action"] = "run_cmd"
    else:
        context.bot.send_message(chat_id=chat_id, text="Команда не разрешена!")

# Telegram handlers
def start(update, context):
    update.message.reply_text(
        "Привет! Я бот-ассистент для разработки. Доступные команды:\n"
        "- Создай <файл> <задача> - создать новый файл\n"
        "- Запустить <файл> - выполнить скрипт\n"
        "- cmd: <команда> - выполнить системную команду\n"
        "- Исправить ошибки <файл> - анализ и исправление кода"
    )

def handle_message(update, context):
    chat_id = update.message.chat_id
    message = update.message.text.lower()

    # Анализ проекта для контекста
    context_str = analyze_project(config.PROJECT_DIR)
    
    try:
        if message.startswith("создай"):
            match = re.match(r"создай\s+(\S+)\s+(.+)", message)
            if match:
                output_file, task = match.groups()
                output_path = os.path.join(config.PROJECT_DIR, output_file)
                code = llm_client.call(task, context_str)
                success, result = save_code(code, output_path)
                if success:
                    update.message.reply_text(f"Код сохранён в {result}:\n{code[:1000]}...")
                    run_script(output_path, chat_id, context)
                else:
                    update.message.reply_text(result)
            else:
                update.message.reply_text("Формат: 'Создай файл.py задача'")

        elif message.startswith("запустить"):
            file_path = os.path.join(config.PROJECT_DIR, message.split()[-1])
            run_script(file_path, chat_id, context)

        elif message.startswith("cmd:"):
            command = message[4:].strip()
            run_cmd(command, chat_id, context)

        elif message.startswith("исправить ошибки"):
            file_path = os.path.join(config.PROJECT_DIR, message.split()[-1])
            if os.path.exists(file_path):
                with open(file_path, "r", encoding="utf-8") as f:
                    code = f.read()
                result = subprocess.run(
                    f"python {file_path}",
                    capture_output=True,
                    text=True,
                    shell=True
                )
                if result.stderr:
                    fixed_code = llm_client.call(
                        f"Исправь ошибки в коде:\n{code}\nОшибки:\n{result.stderr}",
                        context_str
                    )
                    success, result = save_code(fixed_code, file_path)
                    update.message.reply_text(
                        f"Исправленный код сохранён:\n{fixed_code[:1000]}..." 
                        if success else result
                    )
                else:
                    update.message.reply_text("Ошибок не найдено.")
            else:
                update.message.reply_text("Файл не найден.")

        else:
            response = llm_client.call(message, context_str)
            update.message.reply_text(response[:4000])  # Ограничение Telegram

    except Exception as e:
        logging.error(f"Ошибка обработки сообщения: {e}")
        update.message.reply_text("Произошла ошибка при обработке запроса")

def button_callback(update, context):
    query = update.callback_query
    query.answer()
    chat_id = query.message.chat_id
    data = query.data

    try:
        if data == "cancel":
            context.bot.send_message(chat_id=chat_id, text="Действие отменено.")
            context.user_data.clear()

        elif data.startswith("run_script:"):
            file_path = data.split(":", 1)[1]
            install_dependencies(os.path.join(config.PROJECT_DIR, "requirements.txt"))
            result = subprocess.run(
                f"python {file_path}",
                capture_output=True,
                text=True,
                shell=True
            )
            output = f"Результат:\n{result.stdout[:3000]}"
            if result.stderr:
                output += f"\nОшибки:\n{result.stderr[:1000]}"
            context.bot.send_message(chat_id=chat_id, text=output)
            context.user_data.clear()

        elif data.startswith("run_cmd:"):
            command = data.split(":", 1)[1]
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                shell=True
            )
            output = f"Результат:\n{result.stdout[:3000]}"
            if result.stderr:
                output += f"\nОшибки:\n{result.stderr[:1000]}"
            context.bot.send_message(chat_id=chat_id, text=output)
            context.user_data.clear()

    except Exception as e:
        logging.error(f"Ошибка обработки callback: {e}")
        context.bot.send_message(chat_id=chat_id, text="Ошибка выполнения команды")

def main():
    # Инициализация LLM клиента
    global llm_client
    llm_client = LLMClient()
    llm_client.initialize(config.USE_GIGACHAT)

    # Запуск Telegram бота
    updater = Updater(config.TELEGRAM_TOKEN, use_context=True)
    dp = updater.dispatcher
    
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    dp.add_handler(CallbackQueryHandler(button_callback))
    
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()